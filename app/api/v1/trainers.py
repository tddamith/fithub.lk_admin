from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from datetime import datetime
from bson import ObjectId
from typing import List, Optional
import json
import os
import shutil
from pathlib import Path

from app.db.database import mongo
from app.api.v1.schemas.trainer_schema import (
    TrainerCreate,
    TrainerUpdate,
    TrainerInDB,
    TrainerBasic
)

router = APIRouter()

# Create upload directories
UPLOAD_DIR = Path("uploads")
PROFILE_PHOTO_DIR = UPLOAD_DIR / "profile_photos"
INTRO_VIDEO_DIR = UPLOAD_DIR / "intro_videos"

for dir_path in [UPLOAD_DIR, PROFILE_PHOTO_DIR, INTRO_VIDEO_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


async def save_upload_file(upload_file: UploadFile, subdirectory: str) -> dict:
    """Save uploaded file and return file info"""
    try:
        file_extension = os.path.splitext(upload_file.filename)[1]
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ObjectId()}{file_extension}"

        if subdirectory == "profile_photos":
            save_dir = PROFILE_PHOTO_DIR
        elif subdirectory == "intro_videos":
            save_dir = INTRO_VIDEO_DIR
        else:
            save_dir = UPLOAD_DIR / subdirectory
            save_dir.mkdir(parents=True, exist_ok=True)

        file_path = save_dir / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        return {
            "file_name": upload_file.filename,
            "file_url": f"/uploads/{subdirectory}/{unique_filename}",
            "file_size": str(os.path.getsize(file_path))
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


async def delete_upload_file(file_url: str):
    """Delete uploaded file"""
    try:
        if file_url and file_url.startswith("/uploads/"):
            file_path = Path(file_url.lstrip("/"))
            if file_path.exists():
                file_path.unlink()
    except Exception as e:
        print(f"Error deleting file: {str(e)}")


# ── Create new trainer (JSON, no files) ───────────────────────────────────────
@router.post("/create/new/trainer", response_model=dict)
async def create_trainer(trainer: TrainerCreate):
    """Create a new trainer."""
    try:
        trainer_collection = await mongo.get_collection("trainers")

        existing_trainer = await trainer_collection.find_one({
            "full_name": trainer.full_name,
            "primary_specialization": trainer.primary_specialization
        })
        if existing_trainer:
            raise HTTPException(
                status_code=400,
                detail="Trainer with similar name and specialization already exists."
            )

        trainer_id = str(ObjectId())
        current_time = datetime.utcnow()

        trainer_data = {
            "trainer_id": trainer_id,
            "full_name": trainer.full_name,
            "experience": trainer.experience,
            "primary_specialization": trainer.primary_specialization,
            "languages": trainer.languages,
            "short_bio": trainer.short_bio,
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
            "status": "active",
            "created_at": current_time,
            "updated_at": current_time,
        }

        await trainer_collection.insert_one(trainer_data)
        # FIX: convert ObjectId injected by MongoDB to string before returning
        trainer_data["_id"] = str(trainer_data["_id"])

        return {
            "message": "Trainer created successfully",
            "trainer_id": trainer_id,
            "trainer_data": trainer_data
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# ── Create new trainer with media files (multipart) ───────────────────────────
@router.post("/create/new/trainer/with-media", response_model=dict)
async def create_trainer_with_media(
    full_name: str = Form(...),
    experience: int = Form(...),
    primary_specialization: str = Form(...),
    languages: str = Form(...),
    short_bio: str = Form(...),
    skills: str = Form(...),
    certifications: str = Form(...),
    preferred_mode: str = Form(...),
    weekly_schedule: str = Form(...),
    pricing: str = Form(...),
    media: str = Form(...),
    profile_photo: Optional[UploadFile] = File(None),
    intro_video: Optional[UploadFile] = File(None),
):
    """Create a new trainer with file uploads."""
    try:
        languages_list = json.loads(languages)
        skills_dict = json.loads(skills)
        certifications_list = json.loads(certifications)
        preferred_mode_dict = json.loads(preferred_mode)
        weekly_schedule_list = json.loads(weekly_schedule)
        pricing_dict = json.loads(pricing)
        media_dict = json.loads(media)

        trainer_collection = await mongo.get_collection("trainers")

        existing_trainer = await trainer_collection.find_one({
            "full_name": full_name,
            "primary_specialization": primary_specialization
        })
        if existing_trainer:
            raise HTTPException(
                status_code=400,
                detail="Trainer with similar name and specialization already exists."
            )

        if profile_photo:
            info = await save_upload_file(profile_photo, "profile_photos")
            media_dict["profile_photo_url"] = info["file_url"]
            media_dict["profile_photo_name"] = info["file_name"]

        if intro_video:
            info = await save_upload_file(intro_video, "intro_videos")
            media_dict["intro_video_url"] = info["file_url"]
            media_dict["intro_video_name"] = info["file_name"]

        trainer_id = str(ObjectId())
        current_time = datetime.utcnow()

        trainer_data = {
            "trainer_id": trainer_id,
            "full_name": full_name,
            "experience": experience,
            "primary_specialization": primary_specialization,
            "languages": languages_list,
            "short_bio": short_bio,
            "skills": skills_dict,
            "certifications": certifications_list,
            "preferred_mode": preferred_mode_dict,
            "weekly_schedule": weekly_schedule_list,
            "pricing": pricing_dict,
            "media": media_dict,
            "status": "active",
            "created_at": current_time,
            "updated_at": current_time,
        }

        await trainer_collection.insert_one(trainer_data)
        # FIX: convert ObjectId injected by MongoDB to string before returning
        trainer_data["_id"] = str(trainer_data["_id"])

        return {
            "message": "Trainer created successfully with media",
            "trainer_id": trainer_id,
            "trainer_data": trainer_data
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# ── Save trainer as draft (JSON) ──────────────────────────────────────────────
@router.post("/save/draft/trainer", response_model=dict)
async def save_trainer_draft(trainer: TrainerCreate):
    """Save trainer as draft."""
    try:
        trainer_collection = await mongo.get_collection("trainers")

        trainer_id = str(ObjectId())
        current_time = datetime.utcnow()

        trainer_data = trainer.dict()
        trainer_data["trainer_id"] = trainer_id
        trainer_data["status"] = "draft"
        trainer_data["created_at"] = current_time
        trainer_data["updated_at"] = current_time

        if "media" in trainer_data:
            trainer_data["media"]["publish_status"] = "draft"

        await trainer_collection.insert_one(trainer_data)
        # FIX: convert ObjectId to string
        trainer_data["_id"] = str(trainer_data["_id"])

        return {
            "message": "Draft saved successfully",
            "trainer_id": trainer_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# ── Save draft with media files (multipart) ───────────────────────────────────
@router.post("/save/draft/trainer/with-media", response_model=dict)
async def save_trainer_draft_with_media(
    full_name: str = Form(...),
    experience: int = Form(...),
    primary_specialization: str = Form(...),
    languages: str = Form(...),
    short_bio: str = Form(...),
    skills: str = Form(...),
    certifications: str = Form(...),
    preferred_mode: str = Form(...),
    weekly_schedule: str = Form(...),
    pricing: str = Form(...),
    media: str = Form(...),
    profile_photo: Optional[UploadFile] = File(None),
    intro_video: Optional[UploadFile] = File(None),
):
    """Save trainer as draft with file uploads."""
    try:
        languages_list = json.loads(languages)
        skills_dict = json.loads(skills)
        certifications_list = json.loads(certifications)
        preferred_mode_dict = json.loads(preferred_mode)
        weekly_schedule_list = json.loads(weekly_schedule)
        pricing_dict = json.loads(pricing)
        media_dict = json.loads(media)

        trainer_collection = await mongo.get_collection("trainers")

        if profile_photo:
            info = await save_upload_file(profile_photo, "profile_photos")
            media_dict["profile_photo_url"] = info["file_url"]
            media_dict["profile_photo_name"] = info["file_name"]

        if intro_video:
            info = await save_upload_file(intro_video, "intro_videos")
            media_dict["intro_video_url"] = info["file_url"]
            media_dict["intro_video_name"] = info["file_name"]

        trainer_id = str(ObjectId())
        current_time = datetime.utcnow()

        trainer_data = {
            "trainer_id": trainer_id,
            "full_name": full_name,
            "experience": experience,
            "primary_specialization": primary_specialization,
            "languages": languages_list,
            "short_bio": short_bio,
            "skills": skills_dict,
            "certifications": certifications_list,
            "preferred_mode": preferred_mode_dict,
            "weekly_schedule": weekly_schedule_list,
            "pricing": pricing_dict,
            "media": {
                **media_dict,
                "publish_status": "draft"
            },
            "status": "draft",
            "created_at": current_time,
            "updated_at": current_time,
        }

        await trainer_collection.insert_one(trainer_data)

        return {
            "message": "Draft saved successfully with media",
            "trainer_id": trainer_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# ── Publish trainer ────────────────────────────────────────────────────────────
@router.patch("/publish/trainer/{trainer_id}", response_model=dict)
async def publish_trainer(trainer_id: str):
    """Publish a draft trainer."""
    try:
        trainer_collection = await mongo.get_collection("trainers")

        existing_trainer = await trainer_collection.find_one({"trainer_id": trainer_id})
        if not existing_trainer:
            raise HTTPException(status_code=404, detail="Trainer not found")

        result = await trainer_collection.update_one(
            {"trainer_id": trainer_id},
            {"$set": {
                "status": "active",
                "media.publish_status": "active",
                "updated_at": datetime.utcnow()
            }}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Trainer not found")

        return {"message": "Trainer published successfully"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# ── Get all trainers with pagination ──────────────────────────────────────────
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

        filter_query = {}
        if status:
            filter_query["status"] = status
        else:
            # By default exclude deleted trainers
            filter_query["status"] = {"$ne": "deleted"}
        if specialization:
            filter_query["primary_specialization"] = specialization

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
            "total_pages": (total_count + limit - 1) // limit
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# ── Get trainer by ID ─────────────────────────────────────────────────────────
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


# ── Update trainer (JSON) ─────────────────────────────────────────────────────
@router.put("/update/trainer/{trainer_id}", response_model=dict)
async def update_trainer(trainer_id: str, trainer_update: TrainerUpdate):
    """Update an existing trainer."""
    try:
        trainer_collection = await mongo.get_collection("trainers")

        existing_trainer = await trainer_collection.find_one({"trainer_id": trainer_id})
        if not existing_trainer:
            raise HTTPException(status_code=404, detail="Trainer not found.")

        update_data = {"updated_at": datetime.utcnow()}

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

        if trainer_update.pricing is not None:
            update_data["pricing"] = {
                "per_session": trainer_update.pricing.per_session,
                "weekly_plan": trainer_update.pricing.weekly_plan,
                "monthly_plan": trainer_update.pricing.monthly_plan,
                "currency": trainer_update.pricing.currency,
            }

        if trainer_update.media is not None:
            if existing_trainer.get("media"):
                old_media = existing_trainer["media"]
                if trainer_update.media.profile_photo_url is None and old_media.get("profile_photo_url"):
                    await delete_upload_file(old_media["profile_photo_url"])
                if trainer_update.media.intro_video_url is None and old_media.get("intro_video_url"):
                    await delete_upload_file(old_media["intro_video_url"])

            update_data["media"] = {
                "profile_photo_url": trainer_update.media.profile_photo_url,
                "profile_photo_name": trainer_update.media.profile_photo_name,
                "intro_video_url": trainer_update.media.intro_video_url,
                "intro_video_name": trainer_update.media.intro_video_name,
                "publish_status": trainer_update.media.publish_status,
            }

        if trainer_update.status is not None:
            update_data["status"] = trainer_update.status

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


# ── Update trainer with media files (multipart) ───────────────────────────────
@router.put("/update/trainer/{trainer_id}/with-media", response_model=dict)
async def update_trainer_with_media(
    trainer_id: str,
    full_name: Optional[str] = Form(None),
    experience: Optional[int] = Form(None),
    primary_specialization: Optional[str] = Form(None),
    languages: Optional[str] = Form(None),
    short_bio: Optional[str] = Form(None),
    skills: Optional[str] = Form(None),
    certifications: Optional[str] = Form(None),
    preferred_mode: Optional[str] = Form(None),
    weekly_schedule: Optional[str] = Form(None),
    pricing: Optional[str] = Form(None),
    media: Optional[str] = Form(None),
    profile_photo: Optional[UploadFile] = File(None),
    intro_video: Optional[UploadFile] = File(None),
):
    """Update an existing trainer with file uploads."""
    try:
        trainer_collection = await mongo.get_collection("trainers")

        existing_trainer = await trainer_collection.find_one({"trainer_id": trainer_id})
        if not existing_trainer:
            raise HTTPException(status_code=404, detail="Trainer not found.")

        update_data = {"updated_at": datetime.utcnow()}

        if full_name is not None:
            update_data["full_name"] = full_name
        if experience is not None:
            update_data["experience"] = experience
        if primary_specialization is not None:
            update_data["primary_specialization"] = primary_specialization
        if short_bio is not None:
            update_data["short_bio"] = short_bio
        if languages:
            update_data["languages"] = json.loads(languages)
        if skills:
            update_data["skills"] = json.loads(skills)
        if preferred_mode:
            update_data["preferred_mode"] = json.loads(preferred_mode)
        if weekly_schedule:
            update_data["weekly_schedule"] = json.loads(weekly_schedule)
        if pricing:
            update_data["pricing"] = json.loads(pricing)
        if certifications:
            update_data["certifications"] = json.loads(certifications)

        media_dict = json.loads(media) if media else existing_trainer.get("media", {})

        if profile_photo:
            if existing_trainer.get("media", {}).get("profile_photo_url"):
                await delete_upload_file(existing_trainer["media"]["profile_photo_url"])
            info = await save_upload_file(profile_photo, "profile_photos")
            media_dict["profile_photo_url"] = info["file_url"]
            media_dict["profile_photo_name"] = info["file_name"]

        if intro_video:
            if existing_trainer.get("media", {}).get("intro_video_url"):
                await delete_upload_file(existing_trainer["media"]["intro_video_url"])
            info = await save_upload_file(intro_video, "intro_videos")
            media_dict["intro_video_url"] = info["file_url"]
            media_dict["intro_video_name"] = info["file_name"]

        update_data["media"] = media_dict

        await trainer_collection.update_one(
            {"trainer_id": trainer_id},
            {"$set": update_data}
        )

        return {"message": "Trainer updated successfully with media"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# ── Delete trainer (soft delete) ──────────────────────────────────────────────
@router.delete("/delete/trainer/{trainer_id}", response_model=dict)
async def delete_trainer(trainer_id: str):
    """Delete a trainer (soft delete — status set to 'deleted')."""
    try:
        trainer_collection = await mongo.get_collection("trainers")

        existing_trainer = await trainer_collection.find_one({"trainer_id": trainer_id})
        if not existing_trainer:
            raise HTTPException(status_code=404, detail="Trainer not found.")

        result = await trainer_collection.update_one(
            {"trainer_id": trainer_id},
            {"$set": {"status": "deleted", "updated_at": datetime.utcnow()}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Trainer not found.")

        return {"message": "Trainer deleted successfully"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# ── Hard delete trainer (permanent) ──────────────────────────────────────────
@router.delete("/hard-delete/trainer/{trainer_id}", response_model=dict)
async def hard_delete_trainer(trainer_id: str):
    """Permanently delete a trainer and all associated files."""
    try:
        trainer_collection = await mongo.get_collection("trainers")

        trainer = await trainer_collection.find_one({"trainer_id": trainer_id})
        if not trainer:
            raise HTTPException(status_code=404, detail="Trainer not found.")

        if trainer.get("media"):
            if trainer["media"].get("profile_photo_url"):
                await delete_upload_file(trainer["media"]["profile_photo_url"])
            if trainer["media"].get("intro_video_url"):
                await delete_upload_file(trainer["media"]["intro_video_url"])

        result = await trainer_collection.delete_one({"trainer_id": trainer_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Trainer not found.")

        return {"message": "Trainer permanently deleted"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# ── Get trainers by specialization ────────────────────────────────────────────
@router.get("/get/trainers/by/specialization/{specialization}", response_model=dict)
async def get_trainers_by_specialization(
    specialization: str,
    page: int = 1,
    limit: int = 10
):
    """Get trainers by their primary specialization."""
    try:
        trainer_collection = await mongo.get_collection("trainers")

        filter_query = {"primary_specialization": specialization, "status": "active"}
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


# ── Get trainers by status ────────────────────────────────────────────────────
@router.get("/get/trainers/by/status/{status}", response_model=dict)
async def get_trainers_by_status(
    status: str,
    page: int = 1,
    limit: int = 10
):
    """Get trainers by status (active, draft, deleted)."""
    try:
        trainer_collection = await mongo.get_collection("trainers")

        filter_query = {"status": status}
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
            "status": status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# ── Search trainers ───────────────────────────────────────────────────────────
@router.get("/search/trainers", response_model=dict)
async def search_trainers(
    query: Optional[str] = None,
    min_experience: Optional[int] = None,
    max_experience: Optional[int] = None,
    languages: Optional[str] = None,
    skills: Optional[str] = None,
    specialization: Optional[str] = None,
    status: Optional[str] = "active",
    page: int = 1,
    limit: int = 10
):
    """Advanced search for trainers with multiple filters."""
    try:
        trainer_collection = await mongo.get_collection("trainers")

        filter_query = {}
        if status:
            filter_query["status"] = status
        if query:
            filter_query["$or"] = [
                {"full_name": {"$regex": query, "$options": "i"}},
                {"primary_specialization": {"$regex": query, "$options": "i"}},
                {"short_bio": {"$regex": query, "$options": "i"}},
            ]
        if specialization:
            filter_query["primary_specialization"] = specialization
        if min_experience is not None:
            filter_query["experience"] = {"$gte": min_experience}
        if max_experience is not None:
            filter_query.setdefault("experience", {})["$lte"] = max_experience
        if languages:
            languages_list = json.loads(languages)
            if languages_list:
                filter_query["languages"] = {"$in": languages_list}
        if skills:
            skills_list = json.loads(skills)
            valid_skills = ["hatha_yoga", "mobility_flexibility", "strength_training",
                            "guided_meditation", "rehab_friendly_workouts"]
            skill_queries = [
                {f"skills.{s.lower().replace(' ', '_')}": True}
                for s in skills_list
                if s.lower().replace(" ", "_") in valid_skills
            ]
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
            "total_pages": (total_count + limit - 1) // limit,
            "filters_applied": {
                "query": query,
                "min_experience": min_experience,
                "max_experience": max_experience,
                "languages": json.loads(languages) if languages else None,
                "skills": json.loads(skills) if skills else None,
                "specialization": specialization,
                "status": status
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# ── Trainer statistics ─────────────────────────────────────────────────────────
@router.get("/trainers/statistics", response_model=dict)
async def get_trainer_statistics():
    """Get statistics about trainers."""
    try:
        trainer_collection = await mongo.get_collection("trainers")

        total_active = await trainer_collection.count_documents({"status": "active"})
        total_draft = await trainer_collection.count_documents({"status": "draft"})
        total_deleted = await trainer_collection.count_documents({"status": "deleted"})

        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$primary_specialization", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]

        specialization_stats = []
        async for doc in trainer_collection.aggregate(pipeline):
            specialization_stats.append({
                "specialization": doc["_id"],
                "count": doc["count"]
            })

        return {
            "total_trainers": total_active + total_draft,
            "active": total_active,
            "draft": total_draft,
            "deleted": total_deleted,
            "specialization_distribution": specialization_stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# ── Bulk update trainer status ────────────────────────────────────────────────
@router.patch("/trainers/bulk/status", response_model=dict)
async def bulk_update_trainer_status(
    trainer_ids: List[str],
    status: str
):
    """Update status for multiple trainers."""
    try:
        trainer_collection = await mongo.get_collection("trainers")

        result = await trainer_collection.update_many(
            {"trainer_id": {"$in": trainer_ids}},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )

        return {
            "message": f"Updated {result.modified_count} trainers",
            "matched_count": result.matched_count,
            "modified_count": result.modified_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# ── Get recent trainers ───────────────────────────────────────────────────────
@router.get("/get/recent/trainers", response_model=dict)
async def get_recent_trainers(limit: int = 5):
    """Get most recently created trainers."""
    try:
        trainer_collection = await mongo.get_collection("trainers")

        trainers_cursor = trainer_collection.find().sort("created_at", -1).limit(limit)
        trainers = []

        async for trainer in trainers_cursor:
            trainer["_id"] = str(trainer["_id"])
            trainers.append(trainer)

        return {
            "recent_trainers": trainers,
            "limit": limit
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")