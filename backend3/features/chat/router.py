"""
Chat router: POST /chat/{vector_id}
"""
from fastapi import APIRouter, Depends, HTTPException, status
from deps import get_current_user
from database import documents_col
from features.chat.schemas import ChatRequest, ChatResponse
from features.chat.agent_router import AgentRouter

router = APIRouter(prefix="/chat", tags=["Chat"])
_agent_router = AgentRouter()


@router.post("/{vector_id}", response_model=ChatResponse)
async def chat(
    vector_id: str,
    body: ChatRequest,
    user: dict = Depends(get_current_user),
):
    doc = await documents_col().find_one({"vector_id": vector_id, "user_id": str(user["_id"])})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found or access denied")

    if doc.get("vector_status") != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document not ready yet (status: {doc.get('vector_status')}). Please wait.",
        )

    try:
        result = await _agent_router.ask(vector_id=vector_id, query=body.message)
        return ChatResponse(agent=result["agent"], response=result["response"], vector_id=vector_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(exc)}")
