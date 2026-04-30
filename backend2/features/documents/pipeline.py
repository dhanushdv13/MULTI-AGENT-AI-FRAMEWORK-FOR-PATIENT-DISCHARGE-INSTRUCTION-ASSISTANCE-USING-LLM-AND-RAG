"""
Document processing pipeline — identical OCR strategy to backend/app/ai/processor.py.

Supports:
  • PDF files  — native text + RapidOCR fallback (same as backend)
  • Image files — direct RapidOCR (jpg, jpeg, png, bmp, tiff, webp)
  • Smart chunking preserving paragraph boundaries
  • Saves OCR cache JSON + extracted text file
"""
import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import fitz  # PyMuPDF
from langchain_core.documents import Document
from starlette.concurrency import run_in_threadpool

from rag import embed_instance
from rag.vector_store import VectorStoreManager
import config
from features.documents.service import DocumentService

logger = logging.getLogger("pipeline")

# Image extensions that skip fitz and go straight to OCR
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".gif"}


# ── OCR helpers ─────────────────────────────────────────────────────────────

def _get_ocr_engine():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR()


def _ocr_from_bytes(img_bytes: bytes, ocr_engine) -> Tuple[str, List[Dict]]:
    """Run RapidOCR on raw image bytes. Returns (text, elements_list)."""
    result, _ = ocr_engine(img_bytes)
    if not result:
        return "", []
    text = "\n".join(line[1] for line in result)
    elements = []
    for line in result:
        box, txt, conf = line
        x_coords = [p[0] for p in box]
        y_coords = [p[1] for p in box]
        elements.append({
            "text": txt,
            "x1": min(x_coords), "y1": min(y_coords),
            "x2": max(x_coords), "y2": max(y_coords),
            "conf": float(conf),
        })
    return text, elements


# ── Extraction — PDF ─────────────────────────────────────────────────────────

def extract_from_pdf(file_path: str) -> Tuple[str, List[Dict]]:
    """
    Hybrid PDF extraction (matches backend/app/ai/processor.py):
      - Native text if >= 50 chars per page
      - RapidOCR fallback for scanned/image pages
    Returns: (full_text, pages_data for OCR cache)
    """
    doc = fitz.open(file_path)
    full_text_parts = []
    pages_data = []
    ocr_engine = None

    for page_num, page in enumerate(doc):
        native_text = page.get_text()

        if len(native_text.strip()) < 50:
            logger.info(f"Page {page_num+1}: scanned — running OCR")
            if ocr_engine is None:
                ocr_engine = _get_ocr_engine()
            pix = page.get_pixmap(dpi=300)
            text, elements = _ocr_from_bytes(pix.tobytes("png"), ocr_engine)
            pages_data.append({"text": text, "is_native": False, "elements": elements})
        else:
            text = native_text
            pages_data.append({"text": text, "is_native": True, "elements": []})

        full_text_parts.append(text)

    doc.close()
    return "\n".join(full_text_parts), pages_data


# ── Extraction — Image ───────────────────────────────────────────────────────

def extract_from_image(file_path: str) -> Tuple[str, List[Dict]]:
    """
    Direct OCR on an image file (jpg/png/bmp/tiff/webp).
    Returns: (full_text, pages_data for OCR cache — single page)
    """
    logger.info(f"Image file — running RapidOCR: {file_path}")
    ocr_engine = _get_ocr_engine()
    with open(file_path, "rb") as f:
        img_bytes = f.read()
    text, elements = _ocr_from_bytes(img_bytes, ocr_engine)
    pages_data = [{"text": text, "is_native": False, "elements": elements}]
    return text, pages_data


# ── Smart chunking ───────────────────────────────────────────────────────────

def smart_chunking(text: str, max_chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Chunk text preserving paragraph/semantic boundaries.
    Matches backend/app/ai/processor.py smart_chunking.
    """
    chunks = []
    paragraphs = re.split(r'\n\s*\n', text)
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current_chunk) + len(para) > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + "\n\n" + para
            else:
                chunks.append(para)
                current_chunk = ""
        else:
            if current_chunk:
                current_chunk += "\n\n"
            current_chunk += para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# ── OCR cache + extracted text ───────────────────────────────────────────────

def save_ocr_cache(pages_data: List[Dict], cache_path: str):
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(pages_data, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save OCR cache: {e}")


def save_extracted_text(full_text: str, text_path: str):
    try:
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(full_text)
    except Exception as e:
        logger.error(f"Failed to save extracted text: {e}")


# ── Pipeline ─────────────────────────────────────────────────────────────────

class DocumentPipeline:

    def __init__(self):
        self._svc = DocumentService()

    def _process(self, file_path: str, vector_id: str, doc_id: str) -> Tuple[int, str, str]:
        """
        Synchronous heavy work (runs in threadpool):
          1. Extract text (PDF or image)
          2. Save OCR cache + extracted text
          3. Smart chunk
          4. Build + save FAISS vectorstore
        Returns: (page_count, ocr_cache_path, extracted_text_path)
        """
        ext = Path(file_path).suffix.lower()
        extracted_dir = config.BASE_DIR / "data" / "extracted_content"
        extracted_dir.mkdir(parents=True, exist_ok=True)

        stem = Path(file_path).stem
        ocr_cache_path = str(extracted_dir / f"{stem}_ocr_cache.json")
        extracted_text_path = str(extracted_dir / f"{stem}_extracted.txt")

        # 1. Extract
        if ext in IMAGE_EXTENSIONS:
            full_text, pages_data = extract_from_image(file_path)
        else:
            full_text, pages_data = extract_from_pdf(file_path)

        page_count = len(pages_data)

        if not full_text.strip():
            raise ValueError("No text could be extracted from the document (even with OCR).")

        # 2. Save cache + extracted text
        save_ocr_cache(pages_data, ocr_cache_path)
        save_extracted_text(full_text, extracted_text_path)

        # 3. Chunk
        chunks = smart_chunking(full_text)
        if not chunks:
            raise ValueError("Document produced 0 text chunks — may be empty or image-only.")

        # 4. Convert to LangChain Documents + build FAISS
        lc_docs = [
            Document(
                page_content=chunk,
                metadata={"source": file_path, "chunk_index": i, "doc_id": doc_id},
            )
            for i, chunk in enumerate(chunks)
        ]

        store_path = str(config.VECTORSTORES_DIR / vector_id)
        store = VectorStoreManager(embedding_manager=embed_instance, store_path=store_path)
        store.create_vector_store(lc_docs)
        store.save_vector_store()

        logger.info(f"Indexed {len(lc_docs)} chunks from {page_count} pages → {store_path}")
        return page_count, ocr_cache_path, extracted_text_path

    async def run(self, doc_id: str, user_id: str, file_path: str, vector_id: str):
        try:
            await self._svc.update_status(doc_id, "PROCESSING", "Extracting text (OCR enabled)…")
            page_count, ocr_cache_path, extracted_text_path = await run_in_threadpool(
                self._process, file_path, vector_id, doc_id
            )
            await self._svc.mark_completed(
                doc_id,
                page_count=page_count,
                ocr_cache_path=ocr_cache_path,
                extracted_text_path=extracted_text_path,
            )
        except Exception as exc:
            logger.error(f"Pipeline failed for {doc_id}: {exc}")
            await self._svc.mark_failed(doc_id, str(exc))
