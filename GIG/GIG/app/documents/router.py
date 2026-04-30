"""
Documents Router - Upload, management, and progress tracking endpoints.
Supports concurrent uploads with progress tracking.
"""
import shutil
import logging
from pathlib import Path
from typing import List
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, User, Document, DocumentType as DBDocType
from app.config import settings
from app.auth.utils import get_current_user
from app.documents.schemas import (
    DocumentType,
    DocumentUploadResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentContentResponse,
)

logger = logging.getLogger("documents")

router = APIRouter()

# Shared thread pool for concurrent document processing
# Increased workers for faster parallel uploads (2-4 uploads simultaneously)
import os
_max_workers = min(os.cpu_count() or 4, 8)  # Use CPU cores, max 8
_processing_pool = ThreadPoolExecutor(max_workers=_max_workers, thread_name_prefix="doc_proc")


def _process_and_index_sync(
    doc_id: int,
    file_path: str,
    user_id: int,
    doc_type: str,
    filename: str,
    db_url: str,
):
    """
    Process and index a document (runs in thread pool).
    Pipeline: Extract text -> Chunk -> Embed -> Index -> Generate Word doc
    Uses sync SQLAlchemy because this runs outside the async event loop.
    """
    import time
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.documents.processor import process_document, _update_progress, _clear_progress
    from app.vectorstore.store import add_document_to_index

    engine = create_engine(db_url, echo=False)  # echo=False: no SQL spam
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    start_time = time.time()

    try:
        # Step 1: Extract text, chunk, get metadata
        full_text, chunks, year = process_document(
            file_path, user_id, doc_id, doc_type, filename,
        )

        # Step 2: Update DB with extracted text
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.extracted_text = full_text
            doc.year = year
            doc.processed = 1
            db.commit()

        # Step 3: Add to FAISS vector index
        if chunks:
            _update_progress(doc_id, progress=90, message="Adding to vector index...")
            add_document_to_index(user_id, chunks)

        # Step 4: Generate Word document (so it's ready when user clicks "Download Word")
        _update_progress(doc_id, progress=95, message="Generating Word document...")
        try:
            from pdf_to_word import pdf_to_word
            from pathlib import Path as _Path
            pdf_p = _Path(file_path)
            docx_p = pdf_p.parent / f"{pdf_p.stem}.docx"
            if not docx_p.exists():
                pdf_to_word(str(pdf_p), str(docx_p), dpi=150, max_workers=8)
                logger.info("  Word doc generated: %s", docx_p.name)
        except Exception as word_err:
            logger.warning("  Word doc generation failed (non-fatal): %s", word_err)
            # Non-fatal — user can still view extracted text

        _clear_progress(doc_id)

        elapsed = time.time() - start_time
        logger.info("="*60)
        logger.info("DOCUMENT PROCESSED SUCCESSFULLY")
        logger.info("  File: %s", filename)
        logger.info("  Doc ID: %s | Chunks: %s | Year: %s | Time: %.1fs", doc_id, len(chunks), year, elapsed)
        logger.info("="*60)

    except Exception as e:
        logger.error("="*60)
        logger.error("DOCUMENT PROCESSING FAILED")
        logger.error("  File: %s", filename)
        logger.error("  Doc ID: %s | Error: %s", doc_id, str(e))
        logger.error("="*60)
        import traceback
        traceback.print_exc()

        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.processed = -1
            db.commit()
        # Update progress with error
        from app.documents.processor import _processing_status
        if doc_id in _processing_status:
            _processing_status[doc_id]["status"] = "error"
            _processing_status[doc_id]["message"] = f"Error: {str(e)[:200]}"
    finally:
        db.close()
        engine.dispose()


async def _save_and_queue_upload(
    file: UploadFile,
    doc_type_str: str,
    doc_type_enum: DBDocType,
    doc_type_schema: DocumentType,
    subfolder: str,
    db: AsyncSession,
    current_user: User,
) -> DocumentUploadResponse:
    """Shared upload logic for both discharge and bill uploads."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )

    import uuid
    ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4().hex}{ext}"

    user_dir = settings.USERS_DIR / str(current_user.id) / "uploads" / subfolder
    user_dir.mkdir(parents=True, exist_ok=True)
    file_path = user_dir / unique_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = Document(
        user_id=current_user.id,
        filename=unique_filename,
        original_filename=file.filename,
        doc_type=doc_type_enum,
        file_path=str(file_path),
        processed=0,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Initialize progress tracking
    from app.documents.processor import _update_progress
    _update_progress(doc.id, status="queued", message="Upload complete, queued for processing...")

    # Submit to thread pool (non-blocking, runs concurrently with other uploads)
    _processing_pool.submit(
        _process_and_index_sync,
        doc.id,
        str(file_path),
        current_user.id,
        doc_type_str,
        file.filename,
        settings.DATABASE_URL,
    )

    return DocumentUploadResponse(
        id=doc.id,
        filename=file.filename,
        doc_type=doc_type_schema,
        uploaded_at=doc.uploaded_at,
        processed=False,
        message="Document uploaded. Processing started...",
    )


# ── Upload endpoints ───────────────────────────────────────────────

@router.post("/upload/discharge", response_model=DocumentUploadResponse)
async def upload_discharge_summary(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a discharge summary PDF. Processing runs in background."""
    return await _save_and_queue_upload(
        file, "discharge", DBDocType.DISCHARGE, DocumentType.DISCHARGE,
        "discharge", db, current_user,
    )


@router.post("/upload/bill", response_model=DocumentUploadResponse)
async def upload_hospital_bill(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a hospital bill PDF. Processing runs in background."""
    return await _save_and_queue_upload(
        file, "bill", DBDocType.BILL, DocumentType.BILL,
        "bills", db, current_user,
    )


# ── Progress tracking endpoint ─────────────────────────────────────

@router.get("/progress/{doc_id}")
async def get_document_progress(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get processing progress for a document.
    Frontend polls this every 1-2 seconds to show progress bar.
    
    Returns: { status, progress (0-100), message, total_pages, current_page }
    """
    # Verify document belongs to user
    result = await db.execute(
        select(Document)
        .where(Document.id == doc_id)
        .where(Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check in-memory progress
    from app.documents.processor import get_processing_status
    progress = get_processing_status(doc_id)

    if progress:
        return {
            "doc_id": doc_id,
            "status": progress.get("status", "unknown"),
            "progress": progress.get("progress", 0),
            "total_pages": progress.get("total_pages", 0),
            "current_page": progress.get("current_page", 0),
            "message": progress.get("message", ""),
        }

    # No in-memory progress — check DB
    if doc.processed == 1:
        return {
            "doc_id": doc_id,
            "status": "done",
            "progress": 100,
            "total_pages": 0,
            "current_page": 0,
            "message": "Processing complete",
        }
    elif doc.processed == -1:
        return {
            "doc_id": doc_id,
            "status": "error",
            "progress": 0,
            "total_pages": 0,
            "current_page": 0,
            "message": "Processing failed",
        }
    else:
        return {
            "doc_id": doc_id,
            "status": "pending",
            "progress": 0,
            "total_pages": 0,
            "current_page": 0,
            "message": "Waiting to start...",
        }


# ── List / Get / Delete endpoints ──────────────────────────────────

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents uploaded by the current user."""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
    )
    documents = result.scalars().all()
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=len(documents),
    )


@router.get("/{doc_id}", response_model=DocumentContentResponse)
async def get_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific document with its extracted content."""
    result = await db.execute(
        select(Document)
        .where(Document.id == doc_id)
        .where(Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentContentResponse(
        id=doc.id,
        filename=doc.original_filename,
        doc_type=DocumentType(doc.doc_type.value),
        extracted_text=doc.extracted_text,
        year=doc.year,
        uploaded_at=doc.uploaded_at,
    )


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document, its files, and its FAISS vectors."""
    result = await db.execute(
        select(Document)
        .where(Document.id == doc_id)
        .where(Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc_name = doc.original_filename

    # 1. Delete PDF file and generated files
    try:
        pdf_path = Path(doc.file_path)
        pdf_path.unlink(missing_ok=True)
        # Delete generated .docx and OCR cache
        docx_path = pdf_path.parent / f"{pdf_path.stem}.docx"
        docx_path.unlink(missing_ok=True)
        cache_path = pdf_path.parent / f"{pdf_path.stem}_ocr_cache.json"
        cache_path.unlink(missing_ok=True)
    except Exception:
        pass

    # 2. Delete from FAISS vector index
    try:
        from app.vectorstore.store import get_user_store
        store = get_user_store(current_user.id)
        store.delete_document(doc_id)
        logger.info("Deleted FAISS vectors for doc %s (%s)", doc_id, doc_name)
    except Exception as e:
        logger.warning("Failed to clean FAISS for doc %s: %s", doc_id, e)

    # 3. Delete DB record
    await db.delete(doc)
    await db.commit()

    logger.info("Document deleted: %s (id=%s, user=%s)", doc_name, doc_id, current_user.id)


@router.get("/{doc_id}/word")
async def download_word_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the pre-generated Word document (created during upload processing)."""
    from fastapi.responses import FileResponse

    result = await db.execute(
        select(Document)
        .where(Document.id == doc_id)
        .where(Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pdf_path = Path(doc.file_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")

    docx_path = pdf_path.parent / f"{pdf_path.stem}.docx"

    # Word doc should already exist (generated during upload pipeline)
    # Fallback: generate on-demand if somehow missing
    if not docx_path.exists():
        try:
            from pdf_to_word import pdf_to_word
            logger.info("Word doc missing for doc %s, generating on-demand...", doc_id)
            pdf_to_word(str(pdf_path), str(docx_path), dpi=150, max_workers=8)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to convert PDF to Word: {str(e)}"
            )

    return FileResponse(
        path=str(docx_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{doc.original_filename.replace('.pdf', '')}.docx"
    )
