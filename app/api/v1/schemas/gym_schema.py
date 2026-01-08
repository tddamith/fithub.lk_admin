from pydantic import BaseModel

class GymBase(BaseModel):
    gym_name: str
    category_id: str
    city: str
    distance: float
    address: str
    contact: dict
    booking: dict
    about: str
    facilities: list
    facility_notes: str
    opening_hours: dict
    membership_options: dict
    logo_url: str
    cover_image_url: str
    gallery: list
    status: str