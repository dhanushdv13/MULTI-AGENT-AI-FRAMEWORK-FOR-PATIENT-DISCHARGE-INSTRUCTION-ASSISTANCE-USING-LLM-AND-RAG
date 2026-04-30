from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UploadCreate(BaseModel):
    """Schema for creating a new upload"""
    description: Optional[str] = None
    additional_notes: Optional[str] = None

class UploadOut(BaseModel):
    """Schema for upload response"""
    upload_id: str
    user_id: str
    filename: str
    description: Optional[str]
    file_path: str
    vector_status: str
    vector_id: Optional[str]
    extracted_content: Optional[str]
    additional_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
