from typing import List, Optional, Dict
from pydantic import BaseModel


# Certification Schema
class CertificationSchema(BaseModel):
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[str] = None


# Weekly Schedule Schema
class WeeklyScheduleSchema(BaseModel):
    days: List[str]
    checked: bool
    time_slots: List[str]


# Preferred Mode Schema
class PreferredModeSchema(BaseModel):
    online: bool = False
    in_person: bool = False


# Skills Schema
class SkillsSchema(BaseModel):
    hatha_yoga: bool = False
    mobility_flexibility: bool = False
    strength_training: bool = False
    guided_meditation: bool = False
    rehab_friendly_workouts: bool = False


# Pricing Schema
class PricingSchema(BaseModel):
    per_session: float
    weekly_plan: Optional[float] = None
    monthly_plan: Optional[float] = None
    currency: str = "LKR"


# Media Schema
class MediaSchema(BaseModel):
    profile_photo_url: Optional[str] = None
    profile_photo_name: Optional[str] = None
    intro_video_url: Optional[str] = None
    intro_video_name: Optional[str] = None
    publish_status: str = "draft"  # "draft" or "active"


# Base Trainer Schema
class TrainerBase(BaseModel):
    # Basic Details
    full_name: str
    experience: int
    primary_specialization: str
    languages: List[str]
    short_bio: str
    
    # Skills & Certifications
    skills: SkillsSchema
    certifications: List[CertificationSchema]
    
    # Availability
    preferred_mode: PreferredModeSchema
    weekly_schedule: List[WeeklyScheduleSchema]
    
    # Pricing & Media
    pricing: PricingSchema
    media: MediaSchema
    
    # Metadata (optional)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    status: Optional[str] = "active"


# Schema for creating a new trainer
class TrainerCreate(TrainerBase):
    pass


# Schema for updating a trainer
class TrainerUpdate(BaseModel):
    full_name: Optional[str] = None
    experience: Optional[int] = None
    primary_specialization: Optional[str] = None
    languages: Optional[List[str]] = None
    short_bio: Optional[str] = None
    skills: Optional[SkillsSchema] = None
    certifications: Optional[List[CertificationSchema]] = None
    preferred_mode: Optional[PreferredModeSchema] = None
    weekly_schedule: Optional[List[WeeklyScheduleSchema]] = None
    pricing: Optional[PricingSchema] = None
    media: Optional[MediaSchema] = None
    status: Optional[str] = None


# Schema for trainer in response (with ID)
class TrainerInDB(TrainerBase):
    id: str


# Schema for trainer list response
class TrainerList(BaseModel):
    trainers: List[TrainerInDB]
    total: int
    page: int
    limit: int


# Simplified schema for dropdowns or basic info
class TrainerBasic(BaseModel):
    id: str
    full_name: str
    primary_specialization: str
    experience: int
    profile_photo_url: Optional[str] = None
    status: str