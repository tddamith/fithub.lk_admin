from fastapi import APIRouter, HTTPException,BackgroundTasks
from datetime import datetime
import asyncio
from app.db.database import mongo
from app.api.v1.schemas.template_schema import TemplateUpdateBase
from app.utils.file_uploader import upload_to_s3_with_progress
import base64
from bson import ObjectId

router = APIRouter()


@router.put("/update/template/by/{template_id}")
async def update_template_zip(
    template_id: str,
    new_file: TemplateUpdateBase,
    background_tasks: BackgroundTasks
):
    try:
        template_collection = await mongo.get_collection("templates")
        job_collection = await mongo.get_collection("jobs")

        template_data = await template_collection.find_one({"template_id": template_id})
        if not template_data:
            raise HTTPException(status_code=404, detail="Template not found")

        job_id = None
        file_url = template_data.get("file_url")

        # ===================================
        # ZIP FILE UPLOAD (only if provided)
        # ===================================
        if new_file.base64_data and new_file.filename:

            if not file_url:
                raise HTTPException(status_code=400, detail="Template has no file_url")

            s3_key = file_url.split(".amazonaws.com/")[-1]

            base64_str = new_file.base64_data.split(",")[-1]
            file_bytes = base64.b64decode(base64_str)

            if not new_file.filename.lower().endswith(".zip"):
                raise HTTPException(status_code=400, detail="Only zip files allowed")

            # Create upload job
            job_id = str(ObjectId())
            await job_collection.insert_one({
                "job_id": job_id,
                "template_id": template_id,
                "type": "update_zip",
                "status": "queued",
                "progress": 0,
                "created_at": datetime.utcnow()
            })

            # Start upload task
            background_tasks.add_task(
                upload_to_s3_with_progress,
                file_bytes,
                s3_key,
                "application/zip",
                job_collection,
                job_id,
            )

        # ===================================
        # NORMAL TEMPLATE DATA UPDATE
        # ===================================
        await template_collection.update_one(
            {"template_id": template_id},
            {
                "$set": {
                    "template_name": new_file.template_name,
                    "category_id": new_file.category_id,
                    "sub_category_id": new_file.sub_category_id,
                    "cover_image": new_file.cover_image.model_dump()
                        if new_file.cover_image else None,
                    "type": new_file.type,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # ===================================
        # RESPONSE
        # ===================================

        if job_id:
            message = "Template updated, ZIP upload started"
        else:
            message = "Template updated "

        return {
            "status": True,
            "message": message,
            "data": {
                "template_id": template_id,
                "job_id": job_id,
                "file_url": file_url
            }
        }

    except Exception as e:
        raise HTTPException(500, f"Error updating: {str(e)}")
