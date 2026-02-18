
from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId
from app.db.database import mongo
from app.api.v1.schemas.trainer_schema import (
    TrainerCreate, 
    TrainerUpdate, 
    TrainerInDB,
    TrainerBasic
)
from typing import List, Optional


router = APIRouter()

# Create new trainer
@router.post("/create/new/trainer", response_model=dict)
async def create_trainer(trainer: TrainerCreate):
    """Create a new trainer."""
    try:
        trainer_collection = await mongo.get_collection("trainers")
        
        # Check if trainer with similar name already exists (optional)
        existing_trainer = await trainer_collection.find_one({
            "full_name": trainer.full_name,
            "primary_specialization": trainer.primary_specialization
        })
        
        if existing_trainer:
            raise HTTPException(
                status_code=400, 
                detail="Trainer with similar name and specialization already exists."
            )
        
        trainer_data = {
            "trainer_id": str(ObjectId()),
            "full_name": trainer.full_name,
            "experience": trainer.experience,
            "primary_specialization": trainer.primary_specialization,
            "languages": trainer.languages,
            "short_bio": trainer.short_bio,
            
            # Skills & Certifications
            "skills": {
                "hatha_yoga": trainer.skills.hatha_yoga,
                "mobility_flexibility": trainer.skills.mobility_flexibility,
                "strength_training": trainer.skills.strength_training,
                "guided_meditation": trainer.skills.guided_meditation,
                "rehab_friendly_workouts": trainer.skills.rehab_friendly_workouts,
            },
            "certifications": [
                {
                    "title": cert.title,
                    "description": cert.description,
                    "file_url": cert.file_url,
                    "file_name": cert.file_name,
                    "file_size": cert.file_size,
                }
                for cert in trainer.certifications
            ],
            
            # Availability
            "preferred_mode": {
                "online": trainer.preferred_mode.online,
                "in_person": trainer.preferred_mode.in_person,
            },
            "weekly_schedule": [
                {
                    "days": schedule.days,
                    "checked": schedule.checked,
                    "time_slots": schedule.time_slots,
                }
                for schedule in trainer.weekly_schedule
            ],
            
            # Pricing & Media
            "pricing": {
                "per_session": trainer.pricing.per_session,
                "weekly_plan": trainer.pricing.weekly_plan,
                "monthly_plan": trainer.pricing.monthly_plan,
                "currency": trainer.pricing.currency,
            },
            "media": {
                "profile_photo_url": trainer.media.profile_photo_url,
                "profile_photo_name": trainer.media.profile_photo_name,
                "intro_video_url": trainer.media.intro_video_url,
                "intro_video_name": trainer.media.intro_video_name,
                "publish_status": trainer.media.publish_status,
            },
            
            # Metadata
            "status": "active",  # Default status
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        result = await trainer_collection.insert_one(trainer_data)
        
        return {
            "message": "Trainer created successfully", 
            "trainer_id": str(result.inserted_id),
            "trainer_data": trainer_data
        }
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Get all trainers with pagination
@router.get("/get/all/trainers", response_model=dict)
async def get_all_trainers(
    page: int = 1, 
    limit: int = 10, 
    status: Optional[str] = None,
    specialization: Optional[str] = None
):
    """Retrieve all trainers with pagination and optional filters."""
    try:
        trainer_collection = await mongo.get_collection("trainers")
        
        # Build filter query
        filter_query = {}
        if status:
            filter_query["status"] = status
        if specialization:
            filter_query["primary_specialization"] = specialization
        
        # Calculate skip
        skip = (page - 1) * limit
        
        # Get total count
        total_count = await trainer_collection.count_documents(filter_query)
        
        # Get trainers with pagination
        trainers_cursor = trainer_collection.find(filter_query).skip(skip).limit(limit)
        trainers = []
        
        async for trainer in trainers_cursor:
            trainer["_id"] = str(trainer["_id"])
            trainers.append(trainer)
        
        return {
            "trainers": trainers,
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Get trainer by ID
@router.get("/get/trainer/{trainer_id}", response_model=dict)
async def get_trainer_by_id(trainer_id: str):
    """Get a specific trainer by ID."""
    try:
        trainer_collection = await mongo.get_collection("trainers")
        
        trainer = await trainer_collection.find_one({"trainer_id": trainer_id})
        
        if not trainer:
            raise HTTPException(status_code=404, detail="Trainer not found.")
        
        trainer["_id"] = str(trainer["_id"])
        return trainer
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Update trainer
@router.put("/update/trainer/{trainer_id}", response_model=dict)
async def update_trainer(trainer_id: str, trainer_update: TrainerUpdate):
    """Update an existing trainer."""
    try:
        trainer_collection = await mongo.get_collection("trainers")
        
        # Check if trainer exists
        existing_trainer = await trainer_collection.find_one({"trainer_id": trainer_id})
        if not existing_trainer:
            raise HTTPException(status_code=404, detail="Trainer not found.")
        
        # Build update dictionary with only provided fields
        update_data = {"updated_at": datetime.utcnow()}
        
        # Basic Details
        if trainer_update.full_name is not None:
            update_data["full_name"] = trainer_update.full_name
        if trainer_update.experience is not None:
            update_data["experience"] = trainer_update.experience
        if trainer_update.primary_specialization is not None:
            update_data["primary_specialization"] = trainer_update.primary_specialization
        if trainer_update.languages is not None:
            update_data["languages"] = trainer_update.languages
        if trainer_update.short_bio is not None:
            update_data["short_bio"] = trainer_update.short_bio
        
        # Skills & Certifications
        if trainer_update.skills is not None:
            update_data["skills"] = {
                "hatha_yoga": trainer_update.skills.hatha_yoga,
                "mobility_flexibility": trainer_update.skills.mobility_flexibility,
                "strength_training": trainer_update.skills.strength_training,
                "guided_meditation": trainer_update.skills.guided_meditation,
                "rehab_friendly_workouts": trainer_update.skills.rehab_friendly_workouts,
            }
        
        if trainer_update.certifications is not None:
            update_data["certifications"] = [
                {
                    "title": cert.title,
                    "description": cert.description,
                    "file_url": cert.file_url,
                    "file_name": cert.file_name,
                    "file_size": cert.file_size,
                }
                for cert in trainer_update.certifications
            ]
        
        # Availability
        if trainer_update.preferred_mode is not None:
            update_data["preferred_mode"] = {
                "online": trainer_update.preferred_mode.online,
                "in_person": trainer_update.preferred_mode.in_person,
            }
        
        if trainer_update.weekly_schedule is not None:
            update_data["weekly_schedule"] = [
                {
                    "days": schedule.days,
                    "checked": schedule.checked,
                    "time_slots": schedule.time_slots,
                }
                for schedule in trainer_update.weekly_schedule
            ]
        
        # Pricing & Media
        if trainer_update.pricing is not None:
            update_data["pricing"] = {
                "per_session": trainer_update.pricing.per_session,
                "weekly_plan": trainer_update.pricing.weekly_plan,
                "monthly_plan": trainer_update.pricing.monthly_plan,
                "currency": trainer_update.pricing.currency,
            }
        
        if trainer_update.media is not None:
            update_data["media"] = {
                "profile_photo_url": trainer_update.media.profile_photo_url,
                "profile_photo_name": trainer_update.media.profile_photo_name,
                "intro_video_url": trainer_update.media.intro_video_url,
                "intro_video_name": trainer_update.media.intro_video_name,
                "publish_status": trainer_update.media.publish_status,
            }
        
        if trainer_update.status is not None:
            update_data["status"] = trainer_update.status
        
        # Perform update
        result = await trainer_collection.update_one(
            {"trainer_id": trainer_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Trainer not found.")
        
        return {"message": "Trainer updated successfully"}
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Delete trainer (soft delete by changing status)
@router.delete("/delete/trainer/{trainer_id}", response_model=dict)
async def delete_trainer(trainer_id: str):
    """Delete a trainer (soft delete - change status to 'deleted')."""
    try:
        trainer_collection = await mongo.get_collection("trainers")
        
        # Check if trainer exists
        existing_trainer = await trainer_collection.find_one({"trainer_id": trainer_id})
        if not existing_trainer:
            raise HTTPException(status_code=404, detail="Trainer not found.")
        
        # Soft delete by updating status
        result = await trainer_collection.update_one(
            {"trainer_id": trainer_id},
            {"$set": {"status": "deleted", "updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Trainer not found.")
        
        return {"message": "Trainer deleted successfully (soft delete)"}
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Hard delete trainer (permanent removal)
@router.delete("/hard-delete/trainer/{trainer_id}", response_model=dict)
async def hard_delete_trainer(trainer_id: str):
    """Permanently delete a trainer from database."""
    try:
        trainer_collection = await mongo.get_collection("trainers")
        
        result = await trainer_collection.delete_one({"trainer_id": trainer_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Trainer not found.")
        
        return {"message": "Trainer permanently deleted"}
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Get trainers by specialization
@router.get("/get/trainers/by/specialization/{specialization}", response_model=dict)
async def get_trainers_by_specialization(
    specialization: str,
    page: int = 1,
    limit: int = 10
):
    """Get trainers by their primary specialization."""
    try:
        trainer_collection = await mongo.get_collection("trainers")
        
        filter_query = {
            "primary_specialization": specialization,
            "status": "active"
        }
        
        skip = (page - 1) * limit
        total_count = await trainer_collection.count_documents(filter_query)
        
        trainers_cursor = trainer_collection.find(filter_query).skip(skip).limit(limit)
        trainers = []
        
        async for trainer in trainers_cursor:
            trainer["_id"] = str(trainer["_id"])
            trainers.append(trainer)
        
        return {
            "trainers": trainers,
            "total": total_count,
            "page": page,
            "limit": limit,
            "specialization": specialization
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Search trainers with multiple filters
@router.get("/search/trainers", response_model=dict)
async def search_trainers(
    query: Optional[str] = None,
    min_experience: Optional[int] = None,
    max_experience: Optional[int] = None,
    languages: Optional[List[str]] = None,
    skills: Optional[List[str]] = None,
    page: int = 1,
    limit: int = 10
):
    """Advanced search for trainers with multiple filters."""
    try:
        trainer_collection = await mongo.get_collection("trainers")
        
        # Build filter query
        filter_query = {"status": "active"}
        
        if query:
            filter_query["$or"] = [
                {"full_name": {"$regex": query, "$options": "i"}},
                {"primary_specialization": {"$regex": query, "$options": "i"}},
                {"short_bio": {"$regex": query, "$options": "i"}},
            ]
        
        if min_experience is not None:
            filter_query["experience"] = {"$gte": min_experience}
        
        if max_experience is not None:
            if "experience" in filter_query:
                filter_query["experience"]["$lte"] = max_experience
            else:
                filter_query["experience"] = {"$lte": max_experience}
        
        if languages:
            filter_query["languages"] = {"$in": languages}
        
        if skills:
            # Convert skills list to skill queries
            skill_queries = []
            for skill in skills:
                skill_field = skill.lower().replace(" ", "_")
                if skill_field in ["hatha_yoga", "mobility_flexibility", "strength_training", 
                                  "guided_meditation", "rehab_friendly_workouts"]:
                    skill_queries.append({f"skills.{skill_field}": True})
            
            if skill_queries:
                filter_query["$and"] = skill_queries
        
        skip = (page - 1) * limit
        total_count = await trainer_collection.count_documents(filter_query)
        
        trainers_cursor = trainer_collection.find(filter_query).skip(skip).limit(limit)
        trainers = []
        
        async for trainer in trainers_cursor:
            trainer["_id"] = str(trainer["_id"])
            trainers.append(trainer)
        
        return {
            "trainers": trainers,
            "total": total_count,
            "page": page,
            "limit": limit,
            "filters_applied": {
                "query": query,
                "min_experience": min_experience,
                "max_experience": max_experience,
                "languages": languages,
                "skills": skills
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")