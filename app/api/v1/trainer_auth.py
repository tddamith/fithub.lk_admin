from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from bson import ObjectId

from app.db.database import mongo
from app.api.v1.schemas.trainer_auth_schema import TrainerSignup, TrainerLogin, VerifyOTP, ResendOTP
from app.utils.validation import (
    generate_salt, generate_password, validate_password,
    generate_signature, refresh_signature, generate_otp,
)
from app.utils.email_sender import send_otp_email

router = APIRouter()

TRAINERS_COL = "trainer_accounts"
GYMS_COL = "gyms"


@router.post("/signup")
async def trainer_signup(data: TrainerSignup):
    try:
        trainers = await mongo.get_collection(TRAINERS_COL)
        gyms = await mongo.get_collection(GYMS_COL)

        if await trainers.find_one({"email": data.email}):
            raise HTTPException(status_code=400, detail="Email already registered")

        gym = await gyms.find_one({"gym_id": data.gym_id})
        if not gym:
            raise HTTPException(status_code=404, detail="Gym not found")

        salt = await generate_salt()
        password_hash = await generate_password(data.password, salt)
        otp = await generate_otp()
        otp_expires_at = (datetime.utcnow() + timedelta(minutes=15)).isoformat()

        trainer_id = str(ObjectId())
        await trainers.insert_one({
            "trainer_id": trainer_id,
            "full_name": data.full_name,
            "email": data.email,
            "phone": data.phone,
            "password": password_hash,
            "salt": salt,
            "gym_id": data.gym_id,
            "primary_specialization": data.primary_specialization,
            "experience": data.experience,
            "is_verified": False,
            "otp": otp,
            "otp_expires_at": otp_expires_at,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        })

        email_sent = send_otp_email(data.email, data.full_name, otp)

        response = {
            "status": True,
            "message": "Signup successful. Please verify your account with the OTP sent to your email.",
            "trainer_id": trainer_id,
        }
        if not email_sent:
            response["otp"] = otp
            response["otp_note"] = "SMTP not configured — OTP exposed for development only."

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.post("/verify")
async def trainer_verify(data: VerifyOTP):
    try:
        trainers = await mongo.get_collection(TRAINERS_COL)

        trainer = await trainers.find_one({"email": data.email})
        if not trainer:
            raise HTTPException(status_code=404, detail="Trainer not found")

        if trainer.get("is_verified"):
            raise HTTPException(status_code=400, detail="Account already verified")

        if trainer.get("otp") != data.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        if datetime.utcnow().isoformat() > trainer.get("otp_expires_at", ""):
            raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")

        await trainers.update_one(
            {"email": data.email},
            {"$set": {
                "is_verified": True,
                "otp": None,
                "otp_expires_at": None,
                "updated_at": datetime.utcnow().isoformat(),
            }},
        )

        payload = {
            "trainer_id": trainer["trainer_id"],
            "email": trainer["email"],
            "role": "trainer",
            "gym_id": trainer["gym_id"],
        }
        token = await generate_signature(dict(payload))
        refresh_token = await refresh_signature(dict(payload))

        return {
            "status": True,
            "message": "Account verified successfully",
            "token": token,
            "refresh_token": refresh_token,
            "trainer": {
                "trainer_id": trainer["trainer_id"],
                "full_name": trainer["full_name"],
                "email": trainer["email"],
                "gym_id": trainer["gym_id"],
                "primary_specialization": trainer["primary_specialization"],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.post("/login")
async def trainer_login(data: TrainerLogin):
    try:
        trainers = await mongo.get_collection(TRAINERS_COL)

        trainer = await trainers.find_one({"email": data.email})
        if not trainer:
            raise HTTPException(status_code=404, detail="Trainer not found")

        if not trainer.get("is_verified"):
            raise HTTPException(status_code=403, detail="Account not verified. Please check your email for the OTP.")

        if trainer.get("status") != "active":
            raise HTTPException(status_code=403, detail="Account is suspended")

        if not await validate_password(trainer["password"], data.password, trainer["salt"]):
            raise HTTPException(status_code=401, detail="Invalid password")

        payload = {
            "trainer_id": trainer["trainer_id"],
            "email": trainer["email"],
            "role": "trainer",
            "gym_id": trainer["gym_id"],
        }
        token = await generate_signature(dict(payload))
        refresh_token = await refresh_signature(dict(payload))

        return {
            "status": True,
            "message": "Login successful",
            "token": token,
            "refresh_token": refresh_token,
            "trainer": {
                "trainer_id": trainer["trainer_id"],
                "full_name": trainer["full_name"],
                "email": trainer["email"],
                "gym_id": trainer["gym_id"],
                "primary_specialization": trainer["primary_specialization"],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.post("/resend-otp")
async def trainer_resend_otp(data: ResendOTP):
    try:
        trainers = await mongo.get_collection(TRAINERS_COL)

        trainer = await trainers.find_one({"email": data.email})
        if not trainer:
            raise HTTPException(status_code=404, detail="Trainer not found")

        if trainer.get("is_verified"):
            raise HTTPException(status_code=400, detail="Account already verified")

        otp = await generate_otp()
        otp_expires_at = (datetime.utcnow() + timedelta(minutes=15)).isoformat()

        await trainers.update_one(
            {"email": data.email},
            {"$set": {
                "otp": otp,
                "otp_expires_at": otp_expires_at,
                "updated_at": datetime.utcnow().isoformat(),
            }},
        )

        email_sent = send_otp_email(data.email, trainer["full_name"], otp)

        response = {"status": True, "message": "OTP resent successfully"}
        if not email_sent:
            response["otp"] = otp
            response["otp_note"] = "SMTP not configured — OTP exposed for development only."

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
