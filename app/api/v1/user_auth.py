from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from bson import ObjectId

from app.db.database import mongo
from app.api.v1.schemas.user_schema import UserSignup, UserLogin, VerifyOTP, ResendOTP
from app.utils.validation import (
    generate_salt, generate_password, validate_password,
    generate_signature, refresh_signature, generate_otp,
)
from app.utils.email_sender import send_otp_email

router = APIRouter()

USERS_COL = "user_accounts"
GYMS_COL = "gyms"


@router.post("/signup")
async def user_signup(data: UserSignup):
    try:
        users = await mongo.get_collection(USERS_COL)
        gyms = await mongo.get_collection(GYMS_COL)

        if await users.find_one({"email": data.email}):
            raise HTTPException(status_code=400, detail="Email already registered")

        gym = await gyms.find_one({"gym_id": data.gym_id})
        if not gym:
            raise HTTPException(status_code=404, detail="Gym not found")

        salt = await generate_salt()
        password_hash = await generate_password(data.password, salt)
        otp = await generate_otp()
        otp_expires_at = (datetime.utcnow() + timedelta(minutes=15)).isoformat()

        user_id = str(ObjectId())
        await users.insert_one({
            "user_id": user_id,
            "full_name": data.full_name,
            "email": data.email,
            "phone": data.phone,
            "password": password_hash,
            "salt": salt,
            "gym_id": data.gym_id,
            "date_of_birth": data.date_of_birth,
            "gender": data.gender,
            "profile_image": None,
            "membership_type": None,
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
            "user_id": user_id,
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
async def user_verify(data: VerifyOTP):
    try:
        users = await mongo.get_collection(USERS_COL)

        user = await users.find_one({"email": data.email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.get("is_verified"):
            raise HTTPException(status_code=400, detail="Account already verified")

        if user.get("otp") != data.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        if datetime.utcnow().isoformat() > user.get("otp_expires_at", ""):
            raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")

        await users.update_one(
            {"email": data.email},
            {"$set": {
                "is_verified": True,
                "otp": None,
                "otp_expires_at": None,
                "updated_at": datetime.utcnow().isoformat(),
            }},
        )

        payload = {
            "user_id": user["user_id"],
            "email": user["email"],
            "role": "user",
            "gym_id": user["gym_id"],
        }
        token = await generate_signature(dict(payload))
        refresh_token = await refresh_signature(dict(payload))

        return {
            "status": True,
            "message": "Account verified successfully",
            "token": token,
            "refresh_token": refresh_token,
            "user": {
                "user_id": user["user_id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "gym_id": user["gym_id"],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.post("/login")
async def user_login(data: UserLogin):
    try:
        users = await mongo.get_collection(USERS_COL)

        user = await users.find_one({"email": data.email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.get("is_verified"):
            raise HTTPException(status_code=403, detail="Account not verified. Please check your email for the OTP.")

        if user.get("status") != "active":
            raise HTTPException(status_code=403, detail="Account is suspended")

        if not await validate_password(user["password"], data.password, user["salt"]):
            raise HTTPException(status_code=401, detail="Invalid password")

        payload = {
            "user_id": user["user_id"],
            "email": user["email"],
            "role": "user",
            "gym_id": user["gym_id"],
        }
        token = await generate_signature(dict(payload))
        refresh_token = await refresh_signature(dict(payload))

        return {
            "status": True,
            "message": "Login successful",
            "token": token,
            "refresh_token": refresh_token,
            "user": {
                "user_id": user["user_id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "gym_id": user["gym_id"],
                "date_of_birth": user.get("date_of_birth"),
                "gender": user.get("gender"),
                "membership_type": user.get("membership_type"),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.post("/resend-otp")
async def user_resend_otp(data: ResendOTP):
    try:
        users = await mongo.get_collection(USERS_COL)

        user = await users.find_one({"email": data.email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.get("is_verified"):
            raise HTTPException(status_code=400, detail="Account already verified")

        otp = await generate_otp()
        otp_expires_at = (datetime.utcnow() + timedelta(minutes=15)).isoformat()

        await users.update_one(
            {"email": data.email},
            {"$set": {
                "otp": otp,
                "otp_expires_at": otp_expires_at,
                "updated_at": datetime.utcnow().isoformat(),
            }},
        )

        email_sent = send_otp_email(data.email, user["full_name"], otp)

        response = {"status": True, "message": "OTP resent successfully"}
        if not email_sent:
            response["otp"] = otp
            response["otp_note"] = "SMTP not configured — OTP exposed for development only."

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
