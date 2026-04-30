"""
Document Pydantic Schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum


class DocumentType(str, Enum):
    """Document type enumeration."""
    DISCHARGE = "discharge"
    BILL = "bill"


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    id: int
    filename: str
    doc_type: DocumentType
    uploaded_at: datetime
    processed: bool
    message: str
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Document details response."""
    id: int
    filename: str
    original_filename: str
    doc_type: DocumentType
    year: Optional[int]
    uploaded_at: datetime
    processed: int  # 0=pending, 1=done, -1=failed
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """List of documents response."""
    documents: List[DocumentResponse]
    total: int


class DocumentContentResponse(BaseModel):
    """Document with extracted content."""
    id: int
    filename: str
    doc_type: DocumentType
    extracted_text: Optional[str]
    year: Optional[int]
    uploaded_at: datetime


class ChunkMetadata(BaseModel):
    """Metadata for a document chunk."""
    user_id: int
    doc_id: int
    doc_type: str
    filename: str
    year: Optional[int]
    page_num: int
    chunk_type: str  # "text" or "table"
    chunk_index: int
