from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from bson import ObjectId

from app.db.database import mongo
from app.api.v1.schemas.owner_schema import OwnerSignup, OwnerLogin, VerifyOTP, ResendOTP
from app.utils.validation import (
    generate_salt, generate_password, validate_password,
    generate_signature, refresh_signature, generate_otp,
)
from app.utils.email_sender import send_otp_email

router = APIRouter()

OWNERS_COL = "owners"
GYMS_COL = "gyms"


@router.post("/signup")
async def owner_signup(data: OwnerSignup):
    try:
        # owners = await mongo.get_collection(OWNERS_COL)
        gyms = await mongo.get_collection(GYMS_COL)

        if await gyms.find_one({"email": data.email}):
            raise HTTPException(status_code=400, detail="Email already registered")

        if await gyms.find_one({"gym_name": data.gym_name}):
            raise HTTPException(status_code=400, detail="Gym name already taken")

        salt = await generate_salt()
        password_hash = await generate_password(data.password, salt)
        otp = await generate_otp()
        otp_expires_at = (datetime.utcnow() + timedelta(minutes=15)).isoformat()

        gym_id = str(ObjectId())
        await gyms.insert_one({
            "gym_id": gym_id,
            "gym_name": data.gym_name,
            # "city": data.city,
            # "address": data.address,
            # "contact": data.contact,
            # "about": data.about,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
        })

        owner_id = str(ObjectId())
        await gyms.insert_one({
            "owner_id": owner_id,
            # "full_name": data.full_name,
            "email": data.email,
            # "phone": data.phone,
            "password": password_hash,
            "salt": salt,
            "gym_id": gym_id,
            "is_verified": False,
            "otp": otp,
            "otp_expires_at": otp_expires_at,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        })

        email_sent = await send_otp_email(data.email, data.gym_name, otp)

        response = {
            "status": True,
            "message": "Signup successful. Please verify your account with the OTP sent to your email.",
            "owner_id": owner_id,
            "gym_id": gym_id,
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
async def owner_verify(data: VerifyOTP):
    try:
        owners = await mongo.get_collection(OWNERS_COL)

        owner = await owners.find_one({"email": data.email})
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")

        if owner.get("is_verified"):
            raise HTTPException(status_code=400, detail="Account already verified")

        if owner.get("otp") != data.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        if datetime.utcnow().isoformat() > owner.get("otp_expires_at", ""):
            raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")

        await owners.update_one(
            {"email": data.email},
            {"$set": {
                "is_verified": True,
                "otp": None,
                "otp_expires_at": None,
                "updated_at": datetime.utcnow().isoformat(),
            }},
        )

        payload = {
            "owner_id": owner["owner_id"],
            "email": owner["email"],
            "role": "owner",
            "gym_id": owner["gym_id"],
        }
        token = await generate_signature(dict(payload))
        refresh_token = await refresh_signature(dict(payload))

        return {
            "status": True,
            "message": "Account verified successfully",
            "token": token,
            "refresh_token": refresh_token,
            "owner": {
                "owner_id": owner["owner_id"],
                "full_name": owner["full_name"],
                "email": owner["email"],
                "gym_id": owner["gym_id"],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.post("/login")
async def owner_login(data: OwnerLogin):
    try:
        owners = await mongo.get_collection('gyms')

        owner = await owners.find_one({"email": data.email})
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")

        if not owner.get("is_verified"):
            raise HTTPException(status_code=403, detail="Account not verified. Please check your email for the OTP.")

        # if owner.get("status") != "active":
        #     raise HTTPException(status_code=403, detail="Account is suspended")

        if not await validate_password(owner["password"], data.password, owner["salt"]):
            raise HTTPException(status_code=401, detail="Invalid password")

        payload = {
            # "owner_id": owner["owner_id"],
            "email": owner["email"],
            "role": "owner",
            "gym_id": owner["gym_id"],
        }
        token = await generate_signature(dict(payload))
        refresh_token = await refresh_signature(dict(payload))

        return {
            "status": True,
            "message": "Login successful",
            "token": token,
            "refresh_token": refresh_token,
            "gym": {
                "role": "owner",
                "gym_name": owner["gym_name"],
                "email": owner["email"],
                "gym_id": owner["gym_id"],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.post("/resend-otp")
async def owner_resend_otp(data: ResendOTP):
    try:
        owners = await mongo.get_collection(OWNERS_COL)

        owner = await owners.find_one({"email": data.email})
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")

        if owner.get("is_verified"):
            raise HTTPException(status_code=400, detail="Account already verified")

        otp = await generate_otp()
        otp_expires_at = (datetime.utcnow() + timedelta(minutes=15)).isoformat()

        await owners.update_one(
            {"email": data.email},
            {"$set": {
                "otp": otp,
                "otp_expires_at": otp_expires_at,
                "updated_at": datetime.utcnow().isoformat(),
            }},
        )

        email_sent = send_otp_email(data.email, owner["full_name"], otp)

        response = {"status": True, "message": "OTP resent successfully"}
        if not email_sent:
            response["otp"] = otp
            response["otp_note"] = "SMTP not configured — OTP exposed for development only."

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
