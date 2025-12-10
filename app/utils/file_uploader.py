import base64
import io
import asyncio
import boto3
import os
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

# AWS Config
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")

# S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)

# Thread executor for uploads
executor = ThreadPoolExecutor()

upload_progress = {}

async def upload_to_s3_with_progress(file_data, filename, content_type, job_collection, job_id):
    file_size = len(file_data)
    upload_progress[job_id] = 0

    async def simulate_progress():
        while upload_progress[job_id] < 95:
            await asyncio.sleep(0.5)
            upload_progress[job_id] += 5
            await job_collection.update_one(
                {"job_id": job_id},
                {"$set": {"progress": upload_progress[job_id]}},
            )

    async def do_upload():
        def _upload():
            s3_client.upload_fileobj(
                io.BytesIO(file_data),
                AWS_BUCKET_NAME,
                filename,
                ExtraArgs={"ContentType": content_type},
            )
        await asyncio.to_thread(_upload)

    # Run both tasks together
    simulate_task = asyncio.create_task(simulate_progress())

    try:
        await do_upload()
        upload_progress[job_id] = 100
        await job_collection.update_one(
            {"job_id": job_id},
            {"$set": {"progress": 100, "status": "completed"}},
        )
    except Exception as e:
        await job_collection.update_one(
            {"job_id": job_id},
            {"$set": {"status": "failed", "error": str(e)}},
        )
    finally:
        simulate_task.cancel()







# ======================================================================================

# --- Progress Tracker ---
# class S3Progress:
#     def __init__(self, filesize, job_collection, job_id):
#         self._filesize = filesize
#         self._seen_so_far = 0
#         self.job_collection = job_collection
#         self.job_id = job_id

#     def __call__(self, bytes_amount):
#         self._seen_so_far += bytes_amount
#         progress = int((self._seen_so_far / self._filesize) * 100)

#         # Schedule progress update in the main loop safely
#         try:
#             loop = asyncio.get_event_loop()
#         except RuntimeError:
#             # Get running loop from FastAPI app (if called from a thread)
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)

#         asyncio.run_coroutine_threadsafe(
#             self.job_collection.update_one(
#                 {"job_id": self.job_id},
#                 {"$set": {"progress": progress}},
#             ),
#             loop,
#         )


# # --- Async Upload Function ---
# async def upload_to_s3_with_progress(file_data, filename, content_type, job_collection, job_id):
#     file_size = len(file_data)
#     progress_callback = S3Progress(file_size, job_collection, job_id)

#     def _upload():
#         try:
#             s3_client.upload_fileobj(
#                 io.BytesIO(file_data),
#                 AWS_BUCKET_NAME,
#                 filename,
#                 ExtraArgs={"ContentType": content_type},
#                 Callback=progress_callback,
#             )
#             # Mark job complete
#             asyncio.run(
#                 job_collection.update_one(
#                     {"job_id": job_id},
#                     {"$set": {"progress": 100, "status": "completed"}},
#                 )
#             )
#         except Exception as e:
#             # Mark job failed
#             asyncio.run(
#                 job_collection.update_one(
#                     {"job_id": job_id},
#                     {"$set": {"status": "failed", "error": str(e)}},
#                 )
#             )

#     # Run upload in background thread
#     await asyncio.to_thread(_upload)



# import io, zipfile, tempfile, asyncio
# from boto3 import client
# from uuid import uuid4
# import boto3
# import os


# AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
# AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
# AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
# AWS_REGION = os.getenv("AWS_REGION")

# s3_client = client(
#     "s3",
#     aws_access_key_id=AWS_ACCESS_KEY,
#     aws_secret_access_key=AWS_SECRET_KEY,
#     region_name=AWS_REGION
# )

# async def process_template_file(file_data, filename, content_type, job_collection, job_id):
#     loop = asyncio.get_running_loop()

#     # --- Stage 1: Upload (0% → 20%) ---
#     file_size = len(file_data)
#     bytes_uploaded = 0

#     def upload_callback(bytes_amount):
#         nonlocal bytes_uploaded
#         bytes_uploaded += bytes_amount
#         progress = int((bytes_uploaded / file_size) * 20)  # scale to 0–20%
#         asyncio.run_coroutine_threadsafe(
#             job_collection.update_one({"job_id": job_id}, {"$set": {"progress": progress, "status": "uploading"}}),
#             loop
#         )

#     def _upload():
#         s3_client.upload_fileobj(io.BytesIO(file_data), AWS_BUCKET_NAME, filename,
#             ExtraArgs={"ContentType": content_type}, Callback=upload_callback)

#     await asyncio.to_thread(_upload)

#     await job_collection.update_one({"job_id": job_id}, {"$set": {"progress": 20, "status": "uploaded"}})

#     # --- Stage 2: Extract ZIP (20% → 90%) ---
#     temp_path = tempfile.mktemp(suffix=".zip")
#     with open(temp_path, "wb") as f:
#         f.write(file_data)

#     with zipfile.ZipFile(temp_path, 'r') as zip_ref:
#         files = zip_ref.infolist()
#         total = len(files)

#         for i, file in enumerate(files):
#             zip_ref.extract(file, f"/tmp/templates/{job_id}")  # change path as needed
#             extract_progress = 20 + int((i / total) * 70)     # 20% → 90%
#             await job_collection.update_one({"job_id": job_id}, {"$set": {"progress": extract_progress, "status": "extracting"}})

#     # --- Stage 3: Finalizing (90% → 100%) ---
#     await job_collection.update_one({"job_id": job_id}, {"$set": {"progress": 100, "status": "completed"}})
