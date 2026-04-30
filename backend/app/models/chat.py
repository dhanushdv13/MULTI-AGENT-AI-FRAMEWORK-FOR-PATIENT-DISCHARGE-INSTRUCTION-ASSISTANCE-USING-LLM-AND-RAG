from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ChatMessage(BaseModel):
    """Schema for chat message request"""
    message: str

class ChatResponse(BaseModel):
    """Schema for chat response"""
    agent: str
    response: str
    vector_id: str

class ChatHistoryItem(BaseModel):
    """Schema for individual history item"""
    role: str
    content: str
    timestamp: datetime
    agent: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    """Schema for history response"""
    history: List[ChatHistoryItem]
