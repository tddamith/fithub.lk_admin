from pydantic import BaseModel
from typing import Optional


class OwnerSignup(BaseModel):
    # full_name: str
    email: str
    # phone: str
    password: str
    gym_name: str
    # city: str
    # address: str
    # contact: dict
    # about: Optional[str] = ""


class OwnerLogin(BaseModel):
    email: str
    password: str


class VerifyOTP(BaseModel):
    email: str
    otp: str


class ResendOTP(BaseModel):
    email: str
