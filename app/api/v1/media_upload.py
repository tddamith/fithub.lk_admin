from fastapi import APIRouter, HTTPException
from app.api.v1.schemas.image_upload import ImageUpload
from app.db.database import mongo
from app.utils.file_uploader import upload_to_s3_with_progress
from datetime import datetime
from bson import ObjectId
from uuid import uuid4
import boto3
import base64
import os
import io
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from botocore.config import Config

# Load env
load_dotenv()

router = APIRouter()

# AWS Config
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")  # MUST be eu-north-1

# Validate env
if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_BUCKET_NAME, AWS_REGION]):
    raise Exception("Missing AWS environment variables")

# S3 Client (fixed config)
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    config=Config(signature_version="s3v4"),
)

# =========================================================
# UPLOAD IMAGE
# =========================================================
@router.post("/upload/image", response_model=dict)
async def upload_image(file: ImageUpload):
    try:
        if not file.base64_data:
            raise HTTPException(status_code=400, detail="No file data provided")
        
        print("Received file:", file.filename, "Type:", file.type)
        print("AWS Config - Bucket:", AWS_BUCKET_NAME, "Region:", AWS_REGION, "Access Key:", AWS_ACCESS_KEY)

        # Remove base64 prefix
        base64_str = file.base64_data.split(",")[1] if "," in file.base64_data else file.base64_data

        # Decode
        try:
            image_data = base64.b64decode(base64_str)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 data")

        # File name
        file_extension = file.filename.split(".")[-1]
        unique_file_name = f"{uuid4()}.{file_extension}"

        # Upload
        s3_client.upload_fileobj(
            io.BytesIO(image_data),
            AWS_BUCKET_NAME,
            unique_file_name,
            ExtraArgs={"ContentType": file.type},
        )

        file_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_file_name}"

        return {
            "file_url": file_url,
            "file_name": unique_file_name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")


# =========================================================
# DELETE IMAGE
# =========================================================
@router.delete("/delete/image/{file_name}", response_model=dict)
async def delete_image(file_name: str):
    try:
        params = {
            "Bucket": AWS_BUCKET_NAME,
            "Key": file_name,
        }

        try:
            s3_client.head_object(**params)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return {
                    "status": False,
                    "message": "File not found",
                    "data": None,
                }
            else:
                raise e

        result = s3_client.delete_object(**params)

        return {
            "status": True,
            "message": "File deleted successfully",
            "data": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")


# =========================================================
# UPLOAD ZIP WITH PROGRESS
# =========================================================
@router.post("/upload/zip", response_model=dict)
async def upload_zip(file: dict):
    try:
        job_collection = await mongo.get_collection("jobs")
        template_files_collection = await mongo.get_collection("template_files")

        template_id = str(ObjectId())
        job_id = str(ObjectId())

        # Insert template
        await template_files_collection.insert_one({
            "template_id": template_id,
            "template_name": file["template_name"],
            "latest_version": file["latest_version"],
            "status": "draft",
            "created_at": datetime.utcnow(),
        })

        # Insert job
        await job_collection.insert_one({
            "job_id": job_id,
            "template_id": template_id,
            "type": "upload_extract",
            "status": "queued",
            "progress": 0,
            "created_at": datetime.utcnow(),
        })

        # Validate file
        if not file.get("base64_data") or not file.get("filename") or not file.get("type"):
            raise HTTPException(status_code=400, detail="Missing file data")

        base64_str = file["base64_data"].split(",")[1] if "," in file["base64_data"] else file["base64_data"]

        try:
            file_data = base64.b64decode(base64_str)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 data")

        # Validate extension
        ext = file["filename"].split(".")[-1].lower()
        if ext != "zip":
            raise HTTPException(status_code=400, detail="Only .zip allowed")

        unique_file_name = f"{uuid4()}.zip"

        # Upload with progress
        await upload_to_s3_with_progress(
            file_data,
            unique_file_name,
            file["type"],
            job_collection,
            job_id
        )

        file_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_file_name}"

        await job_collection.update_one(
            {"job_id": job_id},
            {"$set": {"progress": 100, "status": "completed"}}
        )

        return {
            "file_url": file_url,
            "file_name": unique_file_name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload zip: {str(e)}")