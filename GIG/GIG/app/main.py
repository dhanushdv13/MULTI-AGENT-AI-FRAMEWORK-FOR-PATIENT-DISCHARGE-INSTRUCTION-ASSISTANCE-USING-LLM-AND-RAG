"""
Healthcare Multi-Agent System - FastAPI Application
"""
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.auth.router import router as auth_router
from app.documents.router import router as documents_router
from app.chat.router import router as chat_router

# ── Logging: Clean terminal output with clear visibility ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-15s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
# Silence noisy libraries — keep only app/processor/documents/orchestrator logs
for noisy in [
    "httpcore", "httpx", "urllib3",
    "sqlalchemy", "sqlalchemy.engine", "sqlalchemy.pool", "sqlalchemy.orm",
    "aiosqlite", "aiosqlite.cursor",
    "sentence_transformers", "faiss", "faiss.loader",
    "uvicorn.access",          # Silence per-request HTTP logs
    "multipart", "multipart.multipart",
    "asyncio",                 # Silence asyncio connection errors
]:
    logging.getLogger(noisy).setLevel(logging.ERROR)
# Keep uvicorn.error at INFO — that's where the startup banner lives

app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Multi-Agent Healthcare Assistant for Post-Discharge Support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    import os
    await init_db()
    logger = logging.getLogger("app")
    cpu_cores = os.cpu_count() or 4
    logger.info("="*60)
    logger.info("✓ SERVER STARTED — READY TO ACCEPT REQUESTS")
    logger.info("  API: http://127.0.0.1:8000")
    logger.info("  Frontend: Open frontend/index.html in browser")
    logger.info("  Docs: http://127.0.0.1:8000/docs")
    logger.info("  CPU Cores: %d | OCR Workers: 8 | Upload Workers: %d", 
                cpu_cores, min(cpu_cores, 8))
    logger.info("="*60)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "llm_model": settings.LLM_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
    }


# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(documents_router, prefix="/documents", tags=["Documents"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
