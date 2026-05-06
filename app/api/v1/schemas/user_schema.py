from pydantic import BaseModel
from typing import Optional


class UserSignup(BaseModel):
    full_name: str
    email: str
    phone: str
    password: str
    gym_id: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class VerifyOTP(BaseModel):
    email: str
    otp: str


class ResendOTP(BaseModel):
    email: str
