from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class ImageUpload(BaseModel):
    name: str
    filename: str
    base64_data: str
    type: str
    size: int
    lastModified: int
    lastModifiedDate: str


class ImageUploadResponse(BaseModel):
    key: str
    id: str
    URL: str
    status: Optional[str]
    createdAt: Optional[str]
    message: Optional[str]

