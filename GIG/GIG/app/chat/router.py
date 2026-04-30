"""
Chat Router - Main chat endpoint with SQLite-backed session persistence.
Sessions survive server restarts. Long conversations are auto-summarized.
"""
import logging
import time
import threading
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, User
from app.config import settings
from app.auth.utils import get_current_user

logger = logging.getLogger("chat")

router = APIRouter()


def _get_orchestrator(user_id: int):
    """Lazy-import and create Orchestrator."""
    from app.chat.orchestrator import Orchestrator
    return Orchestrator(user_id)


def _get_agent_type():
    """Lazy-import AgentType enum."""
    from app.chat.orchestrator import AgentType
    return AgentType


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent_detected: str


class SessionHistory(BaseModel):
    session_id: str
    messages: list[ChatMessage]


# ── Main chat endpoint ─────────────────────────────────────────

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Main chat endpoint.
    - Persists messages in SQLite (survives restarts)
    - Builds context from history (with automatic summarization for long chats)
    - Routes to appropriate agent via orchestrator
    """
    from app.chat.session_store import add_message, build_context, maybe_summarize

    logger.info("=" * 60)
    logger.info("[CHAT] User %s (id=%s): %s", current_user.email, current_user.id, request.message[:200])
    logger.info("=" * 60)

    start = time.time()

    # Get or create session
    import uuid
    session_id = request.session_id or uuid.uuid4().hex[:16]

    # Create orchestrator (lazy loaded on first chat)
    orchestrator = _get_orchestrator(current_user.id)

    # Detect intent
    intent, confidence = orchestrator.detect_intent(request.message)
    logger.info("[CHAT] Detected intent: %s (confidence=%.2f)", intent.value, confidence)

    # Build context from persistent session store
    context = build_context(current_user.id, session_id, max_recent=10)
    if context:
        enhanced_query = f"Previous conversation:\n{context}\n\nCurrent question: {request.message}"
    else:
        enhanced_query = request.message

    # Process query
    try:
        response = orchestrator.process_query(enhanced_query)
    except Exception as e:
        logger.error("[CHAT] Error processing query: %s", e, exc_info=True)
        response = f"Sorry, I encountered an error. Please try again. ({str(e)[:100]})"

    elapsed = time.time() - start
    logger.info("[CHAT] Response generated in %.1fs (%d chars)", elapsed, len(response))

    # Save messages to SQLite
    add_message(current_user.id, session_id, "user", request.message)
    add_message(current_user.id, session_id, "assistant", response)

    # Trigger summarization in background if conversation is getting long
    threading.Thread(
        target=maybe_summarize,
        args=(current_user.id, session_id, 20),
        daemon=True,
    ).start()

    return ChatResponse(
        response=response,
        session_id=session_id,
        intent_detected=intent.value,
    )


# ── History endpoints ──────────────────────────────────────────

@router.get("/history/{session_id}", response_model=SessionHistory)
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    from app.chat.session_store import get_recent_messages
    messages = get_recent_messages(current_user.id, session_id, limit=50)
    return SessionHistory(
        session_id=session_id,
        messages=[ChatMessage(**msg) for msg in messages],
    )


@router.delete("/history/{session_id}")
async def clear_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    from app.chat.session_store import clear_session
    clear_session(current_user.id, session_id)
    return {"message": "Session history cleared"}


# ── Specialized direct-access endpoints ────────────────────────

class SummaryRequest(BaseModel):
    action: str = "summary"


@router.post("/discharge/summary")
async def get_discharge_summary(current_user: User = Depends(get_current_user)):
    AT = _get_agent_type()
    orch = _get_orchestrator(current_user.id)
    agent = orch.get_agent(AT.DISCHARGE)
    return {"response": agent.get_summary()}


@router.post("/discharge/medications")
async def get_medications_list(current_user: User = Depends(get_current_user)):
    AT = _get_agent_type()
    orch = _get_orchestrator(current_user.id)
    agent = orch.get_agent(AT.DISCHARGE)
    return {"response": agent.extract_medications()}


@router.post("/bill/analyze")
async def analyze_bill_overcharging(current_user: User = Depends(get_current_user)):
    AT = _get_agent_type()
    orch = _get_orchestrator(current_user.id)
    agent = orch.get_agent(AT.BILL)
    return {"response": agent.analyze_for_overcharging()}


@router.post("/bill/breakdown")
async def get_bill_breakdown(current_user: User = Depends(get_current_user)):
    AT = _get_agent_type()
    orch = _get_orchestrator(current_user.id)
    agent = orch.get_agent(AT.BILL)
    return {"response": agent.get_bill_breakdown()}


@router.post("/medicine/compare-all")
async def compare_all_medicine_prices(current_user: User = Depends(get_current_user)):
    AT = _get_agent_type()
    orch = _get_orchestrator(current_user.id)
    agent = orch.get_agent(AT.MEDICINE)
    return {"response": agent.compare_all_prescribed()}


class MedicinePriceRequest(BaseModel):
    medicine_name: str


@router.post("/medicine/compare")
async def compare_medicine_price(
    request: MedicinePriceRequest,
    current_user: User = Depends(get_current_user),
):
    AT = _get_agent_type()
    orch = _get_orchestrator(current_user.id)
    agent = orch.get_agent(AT.MEDICINE)
    return {"response": agent._compare_prices(request.medicine_name, request.medicine_name)}


class MealPlanRequest(BaseModel):
    days: int = 7


@router.post("/diet/meal-plan")
async def generate_meal_plan(
    request: MealPlanRequest = MealPlanRequest(),
    current_user: User = Depends(get_current_user),
):
    AT = _get_agent_type()
    orch = _get_orchestrator(current_user.id)
    agent = orch.get_agent(AT.DIET)
    return {"response": agent.generate_meal_plan(request.days)}


@router.post("/diet/foods-to-avoid")
async def get_foods_to_avoid(current_user: User = Depends(get_current_user)):
    AT = _get_agent_type()
    orch = _get_orchestrator(current_user.id)
    agent = orch.get_agent(AT.DIET)
    return {"response": agent.foods_to_avoid()}
