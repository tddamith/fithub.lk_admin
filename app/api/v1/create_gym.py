from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime
from bson import ObjectId
from app.db.database import mongo
from app.api.v1.schemas.gym_schema import GymBase
from app.utils.validation import validate_signature
from datetime import datetime,timedelta
from typing import Optional


router = APIRouter()


#create gym
@router.post("/create/new/gym")
async def create_gym(gym: GymBase):
    """Create a new gym."""
    try:
        gym_collection = await mongo.get_collection("gyms")
        
        # Check if gym with the same name already exists
        existing_gym = await gym_collection.find_one({"gym_name": gym.gym_name})
        if existing_gym:
            raise HTTPException(status_code=400, detail="Gym with this name already exists.")
        
        gym_data = {
            "gym_id": str(ObjectId()),
            "gym_name": gym.gym_name,
            "category_id": gym.category_id,
            "city": gym.city,
            "distance": gym.distance,
            "address": gym.address,
            "contact": gym.contact,
            "booking": gym.booking,
            "about": gym.about,
            "facilities": gym.facilities,
            "facility_notes": gym.facility_notes,
            "opening_hours": gym.opening_hours,
            "membership_options": gym.membership_options,
            "logo_url": gym.logo_url,
            "cover_image_url": gym.cover_image_url,
            "gallery": gym.gallery,
            "status": gym.status,
            "created_at": datetime.utcnow()           
        }
        
        result = await gym_collection.insert_one(gym_data)
        
        return {"status": True, "message": "gym created successfully", "gym_id": str(result.inserted_id)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    
#get all gyms
@router.get("/get/all/gyms")
async def get_gyms():
    """Retrieve all gyms."""
    try:
        gym_collection = await mongo.get_collection("gyms")
        
        gyms_cursor = gym_collection.find({})
        gyms = []
        async for gym in gyms_cursor:
            gym["_id"] = str(gym["_id"])  # Convert ObjectId to string
            gyms.append(gym)
        
        return {"gyms": gyms}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    
#update gym
@router.put("/update/gym/by/{gym_id}")
async def update_gym(gym_id: str, gym: GymBase):
    """Update an existing gym."""
    try:
        gym_collection = await mongo.get_collection("gyms")
        
        update_data = {
            "icon_name": gym.icon_name,
            "gym_name": gym.gym_name,
            "updated_at": datetime.utcnow()
        }
        
        result = await gym_collection.update_one(
            {"gym_id": gym_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="gym not found.")
        return {"message": "gym updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    
#delete gym
@router.delete("/delete/gym/by/{gym_id}")
async def delete_gym(gym_id: str):
    """Delete a gym."""
    try:
        gym_collection = await mongo.get_collection("gyms")
        
        result = await gym_collection.delete_one({"gym_id": gym_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="gym not found.")
        return {"message": "gym deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")