from fastapi import APIRouter, HTTPException, Depends
from app.api.v1.schemas.authentication import SignIn
from app.utils.validation import generate_signature, refresh_signature

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
            refresh_token = await refresh_signature({"username": data["username"]})
            print(token)
            
            return {"status": True, "message": "Login Successful", "token": token, "refresh_token": refresh_token}

        return {"status": False, "message": "Invalid username or password"}

    except Exception as e:
        return {"status": False, "message": str(e)}
    
@router.post("/validate-token")
async def refresh_token_endpoint(body: dict):
    try:
        token = body.get("token")
        if not token:
            return {"status": False, "message": "Token is missing"}

        new_token = await generate_signature({"username": "admin"})
        refresh_token = await refresh_signature({"username": "admin"})
        return {"status": True, "message": "Token refreshed successfully", "token": new_token, "refresh_token": refresh_token}

    except Exception as e:
        return {"status": False, "message": str(e)}