
from pydantic import BaseModel, EmailStr

class SignUp(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    account_type: str | None = None
    password: str

class SignIn(BaseModel):
    username: str
    password: str