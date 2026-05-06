from pydantic import BaseModel
from typing import Optional


class TrainerSignup(BaseModel):
    full_name: str
    email: str
    phone: str
    password: str
    gym_id: str
    primary_specialization: str
    experience: Optional[int] = 0


class TrainerLogin(BaseModel):
    email: str
    password: str


class VerifyOTP(BaseModel):
    email: str
    otp: str


class ResendOTP(BaseModel):
    email: str
