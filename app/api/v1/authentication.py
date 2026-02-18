from fastapi import APIRouter, HTTPException, Depends
from app.api.v1.schemas.authentication import SignIn, SignUp
from app.utils.validation import generate_signature, refresh_signature, generate_salt, generate_password
from app.db.database import mongo
from bson import ObjectId
from datetime import datetime
from pymongo.errors import DuplicateKeyError

router = APIRouter()


@router.get("/get/all/users")
async def get_all_users():
    """Retrieve all users (dev/testing endpoint). Removes sensitive fields before returning."""
    try:
        users_collection = await mongo.get_collection("users")
        users_cursor = users_collection.find({})
        users = []
        async for u in users_cursor:
            # remove sensitive fields
            u.pop("_id", None)
            u.pop("password", None)
            u.pop("salt", None)
            users.append(u)
        return {"status": True, "users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sign-in")
async def create_news(user: SignIn):
    try:
        data = user.model_dump()
        if not data["username"] or not data["password"]:
            return {"status": False, "message": "Username or password is empty"}

        # NOTE: replace this with a real user lookup later
        userName = "admin"
        password = "Admin@123"

        if data["username"] == userName and data["password"] == password:
            token = await generate_signature({"username": data["username"]})
            refresh = await refresh_signature({"username": data["username"]})
            return {"status": True, "message": "Login Successful", "token": token, "refresh_token": refresh}

        return {"status": False, "message": "Invalid username or password"}

    except Exception as e:
        return {"status": False, "message": str(e)}


@router.post("/sign-up")
async def sign_up(user: SignUp):
    """Register a new user and store credentials in MongoDB."""
    try:
        data = user.model_dump()

        # basic validation
        if not data.get("email") or not data.get("password") or not data.get("full_name"):
            raise HTTPException(status_code=400, detail="Required fields are missing")

        users_collection = await mongo.get_collection("users")

        # prepare password hash
        salt = await generate_salt()
        hashed_password = await generate_password(data["password"], salt)

        user_doc = {
            "user_id": str(ObjectId()),
            "full_name": data["full_name"],
            "email": data["email"].lower(),
            "phone": data.get("phone"),
            "account_type": data.get("account_type"),
            "password": hashed_password,
            "salt": salt,
            "status": "active",
            "created_at": datetime.utcnow()
        }

        try:
            result = await users_collection.insert_one(user_doc)
        except DuplicateKeyError:
            # this can happen if email index exists and email duplicated
            raise HTTPException(status_code=400, detail="User with this email already exists")

        token = await generate_signature({"email": user_doc["email"], "user_id": user_doc["user_id"]})
        refresh_token = await refresh_signature({"email": user_doc["email"], "user_id": user_doc["user_id"]})

        return {"status": True, "message": "User created successfully", "user_id": user_doc["user_id"], "token": token, "refresh_token": refresh_token}

    except HTTPException as he:
        raise he
    except Exception as e:
        # fallback - if it's a duplicate key error in some environments it may bubble as generic Exception
        msg = str(e)
        if "duplicate key" in msg.lower():
            raise HTTPException(status_code=400, detail="User with this email already exists")
        raise HTTPException(status_code=500, detail=msg)