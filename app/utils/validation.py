import bcrypt
import datetime
import random
from fastapi import Request, HTTPException
from jose import jwt, ExpiredSignatureError, JWTError
import os

# DO NOT generate current time globally. It must be fresh each time.
JWT_SECRET = os.getenv("JWT_SECRET")
#'yNmed6TbrD9i3EM7BjqNtyFp-T5_jlpdcgMLx6S8LCXubTayv27hUK8x9Z'


async def generate_salt() -> str:
    return bcrypt.gensalt().decode()  # Convert to string


async def generate_password(password: str, salt: str) -> str:
    hashed_password = bcrypt.hashpw(password.encode(), salt.encode())
    return hashed_password.decode()


async def validate_password(saved_password: str, entered_password: str, salt: str) -> bool:
    hashed_entered_password = await generate_password(entered_password, salt)
    return hashed_entered_password == saved_password


async def generate_signature(payload: dict) -> str:
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    payload["exp"] = expiration_time
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token


async def generate_otp_signature(payload: dict) -> str:
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    payload["exp"] = expiration_time
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token


async def generate_otp():
    return str(random.randint(1000, 9999))


async def validate_signature(request: Request):
    """Validate JWT token from Authorization header."""
    try:
        signature = request.headers.get("Authorization")

        if not signature:
            raise HTTPException(status_code=401, detail="Authorization token is missing")

        token = signature.replace("Bearer ", "").strip()

        # Verify and decode JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

        # Attach user payload to request state
        request.state.user = payload

        return payload

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


def decode_token(token: str):
    try:
        if not token:
            #print("User details not found....")
            return False

        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded_token

    except ExpiredSignatureError:
        #print("Token has expired.")
        raise HTTPException(status_code=401, detail="Token has expired")

    except JWTError as e:
        #print(f"Invalid token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
