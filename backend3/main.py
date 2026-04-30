"""
FastAPI application — backend2 root entry point.
Run: uvicorn main:app --reload --port 8001
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from database import create_indexes
from features.auth.router import router as auth_router
from features.documents.router import (
    router as documents_router,
    upload_document,
    list_documents,
    get_document,
    download_document,
    content_document,
    get_extracted_text,
    get_extracted_html,
)
from features.chat.router import router as chat_router

app = FastAPI(
    title="AI Insurance Agent API",
    version="2.0",
    description="FastAPI backend with auth, document processing, and multi-agent AI chat.",
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ───────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    await create_indexes()

# ── Routers ───────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)

# ── /uploads/ alias (frontend calls /uploads/ not /documents/) ─
app.add_api_route("/uploads/", upload_document, methods=["POST"], tags=["Uploads (alias)"])
app.add_api_route("/uploads/", list_documents, methods=["GET"], tags=["Uploads (alias)"])
app.add_api_route("/uploads/{doc_id}", get_document, methods=["GET"], tags=["Uploads (alias)"])
app.add_api_route("/uploads/{doc_id}/download", download_document, methods=["GET"], tags=["Uploads (alias)"])
app.add_api_route("/uploads/{doc_id}/content", content_document, methods=["GET"], tags=["Uploads (alias)"])
app.add_api_route("/uploads/{doc_id}/extracted", get_extracted_text, methods=["GET"], tags=["Uploads (alias)"])
app.add_api_route("/uploads/{doc_id}/extracted/html", get_extracted_html, methods=["GET"], tags=["Uploads (alias)"])



@app.get("/", tags=["Health"])
async def health():
    return {"status": "ok", "version": "2.0"}
