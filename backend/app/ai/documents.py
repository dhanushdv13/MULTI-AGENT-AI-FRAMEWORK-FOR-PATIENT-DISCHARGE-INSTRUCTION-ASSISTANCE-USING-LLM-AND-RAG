"""
Document Pydantic Schemas - Adapted for AI Module
"""
from pydantic import BaseModel
from typing import Optional

class ChunkMetadata(BaseModel):
    """Metadata for a document chunk."""
    # Adapted to use str for IDs (MongoDB)
    user_id: str
    upload_id: str  # Renamed from doc_id to match system terminology
    doc_type: str
    filename: str
    year: Optional[int]
    page_num: int
    chunk_type: str  # "text" or "table"
    chunk_index: int
    vector_id: str   # Added vector_id
