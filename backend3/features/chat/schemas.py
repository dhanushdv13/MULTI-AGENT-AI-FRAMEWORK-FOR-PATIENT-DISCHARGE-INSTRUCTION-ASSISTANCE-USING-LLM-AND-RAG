"""
Chat schemas.
"""
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    agent: str
    response: str
    vector_id: str
