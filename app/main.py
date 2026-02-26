from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.create_gym import router as gym_router
from app.api.v1.create_category import router as category_router
from app.api.v1.create_facilities import router as facilities_router
from app.api.v1.media_upload import router as media_uploader_router
from app.api.v1.authentication import router as sign_in_router
from app.api.v1.trainers import router as trainers_router  # This is correct
from app.db.database import connect_all, close_all
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your React frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
async def read_root(request: Request):
    return {"status": "ok", "message": "Fithub API is running"}

@app.on_event("startup")
async def startup_db():
    await connect_all()

@app.on_event("shutdown")
async def shutdown_db():
    await close_all()

# Include routers
app.include_router(gym_router, prefix="/api/v1", tags=["Gyms"])
app.include_router(category_router, prefix="/api/v1", tags=["Categories"])
app.include_router(facilities_router, prefix="/api/v1", tags=["Facilities"])
app.include_router(media_uploader_router, prefix="/api/v1", tags=["media_upload"])
app.include_router(sign_in_router, prefix="/api/v1/auth", tags=["Sign-In"])
app.include_router(trainers_router, prefix="/api/v1", tags=["Trainers"])