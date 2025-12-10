from fastapi import APIRouter, HTTPException, Depends, Request
from app.api.v1.schemas.image_upload import  ImageUpload, ImageUploadResponse
from app.db.database import mongo
from app.utils.file_uploader import upload_to_s3_with_progress
from datetime import datetime
from bson import ObjectId
from uuid import uuid4
import boto3
import base64
import os
import io
from app.utils.validation import validate_signature
from botocore.exceptions import ClientError

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI router
router = APIRouter()

# AWS S3 Configuration
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")

# Initialize S3 Client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)

@router.post("/upload/image", response_model=dict)
async def upload_image(
    # request: Request,
    file: ImageUpload,
    # user: dict = Depends(validate_signature)
    
    ):
    try:
        #print("Received file metadata:", file)

        # Remove the data URL prefix if present (e.g., "data:image/jpeg;base64,")
        if "," in file.base64_data:
            base64_str = file.base64_data.split(",")[1]
        else:
            base64_str = file.base64_data

        # Decode the Base64 data into binary
        image_data = base64.b64decode(base64_str)

        # Generate a unique file name
        file_extension = file.filename.split(".")[-1]
        unique_file_name = f"{uuid4()}.{file_extension}"

        # Upload file to S3
        s3_client.upload_fileobj(
            io.BytesIO(image_data),  # Convert binary data into a file-like object
            AWS_BUCKET_NAME,
            unique_file_name,
            ExtraArgs={"ContentType": file.type},
        )

        # Generate the file URL
        file_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_file_name}"

        print('file_url',file_url)

        return {"file_url": file_url, "file_name": unique_file_name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

#=====================================================================================================
@router.delete("/delete/image/{file_name}", response_model=dict)
async def delete_image(
    # request: Request,
    file_name: str,
    # user: dict = Depends(validate_signature)
    ):

    params = {
        "Bucket": AWS_BUCKET_NAME,
        "Key": file_name,
    }

    try:
        try:
            #Check if file exists
            s3_client.head_object(**params)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return {
                    "status": False,
                    "message": "File not found",
                    "data": None
                }
            else:
                raise e  # re-raise other errors

            # Delete the file from S3
        result = s3_client.delete_object(**params)

        return {
            "status": True,
            "message": "File deleted successfully",
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

# ===========================================================================================================================

@router.post("/upload/zip", response_model=dict)
async def upload_image(
    # request: Request,
    file: dict,
    # user: dict = Depends(validate_signature)
    ):
    try:

        job_collection = await mongo.get_collection("jobs")
        template_files_collection = await mongo.get_collection("template_files")

        template_id = str(ObjectId())
        job_id = str(ObjectId())

        template_data = {
            "template_id": template_id,
            "template_name": file.template_name,
            "latest_version": file.latest_version,
            "status": "draft",
            "created_at": datetime.utcnow(),
        }

        job_data = {
            "job_id": job_id,
            "template_id": template_id,
            "type": "upload_extract",
            "status": "queued",
            "progress": 0,
            "created_at": datetime.utcnow(),
        }

        # Insert records
        await template_files_collection.insert_one(template_data)
        await job_collection.insert_one(job_data)


       # --- File Upload Section ---
        if not file.base64_data or not file.filename or not file.type:
            raise HTTPException(status_code=400, detail="Missing file data.")

        if "," in file.base64_data:
            base64_str = file.base64_data.split(",")[1]
        else:
            base64_str = file.base64_data

        try:
            file_data = base64.b64decode(base64_str)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Base64 data provided.")

        file_extension = file.filename.split(".")[-1].lower()
        print("File extension:", file_extension)
        if file_extension != "zip":
            raise HTTPException(status_code=400, detail="Only .zip files are supported.")

        unique_file_name = f"{uuid4()}.{file_extension}"

        # Upload with progress tracking
        await upload_to_s3_with_progress(file_data, unique_file_name, file.type, job_collection, job_id)

        # Upload done — mark job as completed
        file_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_file_name}"
        await job_collection.update_one(
            {"job_id": job_id},
            {"$set": {"progress": 100, "status": "completed"}}
        )

        print('file_url',file_url)

        return {"file_url": file_url, "file_name": unique_file_name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")
