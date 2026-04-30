from fastapi import APIRouter, Depends, HTTPException
from app.models.chat import ChatMessage, ChatResponse
from app.db.mongo import uploads
from app.core.deps import current_user

router = APIRouter(prefix="/chat", tags=["Chat"])


# Mock agent responses
@router.post("/{vector_id}", response_model=ChatResponse)
async def chat_with_file(
    vector_id: str,
    chat_msg: ChatMessage,
    user=Depends(current_user)
):
    """
    Chat endpoint for specific file context (VectorID Scoped).
    Routes to appropriate agent based on message content.
    """
    # Verify the vector_id belongs to the user
    # Note: We now store vector_id in the upload document
    upload = await uploads.find_one({
        "vector_id": vector_id,
        "user_id": str(user["_id"])
    })
    
    if not upload:
        raise HTTPException(
            status_code=404,
            detail="File context not found or access denied"
        )
    
    try:
        # Initialize Orchestrator with the specific vector_id
        from app.ai.orchestrator import Orchestrator
        orchestrator = Orchestrator(vector_id=vector_id)
        
        # Process the query
        result = await orchestrator.process_query(chat_msg.message)
        
        return ChatResponse(
            agent=result["agent"],
            response=result["response"],
            vector_id=vector_id
        )
        
    except Exception as e:
        print(f"Chat Error: {e}")
        return ChatResponse(
            agent="Error",
            response=f"I encountered an error processing your request: {str(e)}",
            vector_id=vector_id
        )
