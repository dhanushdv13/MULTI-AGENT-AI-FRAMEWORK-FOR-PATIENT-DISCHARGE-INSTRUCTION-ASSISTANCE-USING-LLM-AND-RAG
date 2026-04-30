"""
Pydantic schemas for document endpoints.
"""
from pydantic import BaseModel
from typing import Optional


class UploadStartResponse(BaseModel):
    doc_id: str
    upload_id: str          # alias of doc_id — frontend expects this field name
    vector_id: str
    vector_status: str
    message: str = "Upload started — processing in background"


class DocumentOut(BaseModel):
    doc_id: str
    upload_id: str
    filename: str
    description: Optional[str] = None
    vector_id: str
    vector_status: str
    processing_step: Optional[str] = None
    page_count: int = 0
    ocr_cache_path: Optional[str] = None
    extracted_content_path: Optional[str] = None
