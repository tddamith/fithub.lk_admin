from fastapi import APIRouter, HTTPException, Depends
from app.api.v1.schemas.authentication import SignIn
from app.utils.validation import generate_signature

router = APIRouter()

@router.post("/sign-in")
async def create_news(user: SignIn):
    try:
        data = user.model_dump()
        if not data["username"] or not data["password"]:
            return {"status": False, "message": "Username or password is empty"}
        print(data)

        userName = "admin"
        password = "Admin@123"

        if data["username"] == userName and data["password"] == password:
            print("Login Successful")
            token = await generate_signature({"username": data["username"]})
            print(token)
            return {"status": True, "message": "Login Successful", "token": token}

        return {"status": False, "message": "Invalid username or password"}

    except Exception as e:
        return {"status": False, "message": str(e)}