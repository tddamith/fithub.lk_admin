from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime
from bson import ObjectId
from app.db.database import mongo
from app.api.v1.schemas.facilities_schema import FacilityBase
from app.utils.validation import validate_signature
from datetime import datetime,timedelta
from typing import Optional


router = APIRouter()


#create facility
@router.post("/create/new/facility")
async def create_facility(facility: FacilityBase):
    """Create a new facility."""
    try:
        facility_collection = await mongo.get_collection("facilities")

        # Check if facility with the same name already exists
        existing_facility = await facility_collection.find_one({"facility_name": facility.facility_name})
        if existing_facility:
            raise HTTPException(status_code=400, detail="Facility with this name already exists.")

        facility_data = {
            "facility_id": str(ObjectId()),
            "facility_name": facility.facility_name,
            "status": "new",
            "created_at": datetime.utcnow()           
        }
        
        result = await facility_collection.insert_one(facility_data)

        return {"message": "Facility created successfully", "facility_id": str(result.inserted_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    
#get all facilities
@router.get("/get/all/facilities")
async def get_facilities():
    """Retrieve all facilities."""
    try:
        facility_collection = await mongo.get_collection("facilities")
        
        facilities_cursor = facility_collection.find({})
        facilities = []
        async for facility in facilities_cursor:
            facility["_id"] = str(facility["_id"])  # Convert ObjectId to string
            facilities.append(facility)
        
        return {"facilities": facilities}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    
#update facility
@router.put("/update/facility/by/{facility_id}")
async def update_facility(facility_id: str, facility: FacilityBase):
    """Update an existing facility."""
    try:
        facility_collection = await mongo.get_collection("facilities")
        
        update_data = {
            "icon_name": facility.icon_name,
            "facility_name": facility.facility_name,
            "updated_at": datetime.utcnow()
        }
        
        result = await facility_collection.update_one(
            {"facility_id": facility_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="facility not found.")
        return {"message": "facility updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    
#delete facility
@router.delete("/delete/facility/by/{facility_id}")
async def delete_facility(facility_id: str):
    """Delete a facility."""
    try:
        facility_collection = await mongo.get_collection("facilities")
        
        result = await facility_collection.delete_one({"facility_id": facility_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="facility not found.")
        return {"message": "facility deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")