from fastapi import APIRouter, HTTPException
from app.db.database import mongo


# Initialize FastAPI router
router = APIRouter()

@router.get("/get/progress/by/{job_id}")

async def get_job_progress(job_id:str):
    try:
        print("jobid",job_id)
        job_collection = await mongo.get_collection("jobs")

        jobs_cursor = await job_collection.find_one({"job_id": job_id}) 

        if not jobs_cursor:
            raise HTTPException(status_code=404, detail="Job not found")
       
        
        jobs_cursor["_id"] = str(jobs_cursor["_id"])         
        
        return {"status": True,"progress": jobs_cursor.get("progress", 0)}
    
    

    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")