"""
Document Processor - PDF extraction and smart chunking
OPTIMIZED: Native text first, parallel OCR, OCR cache for pdf_to_word reuse.
"""
import os
import re
import json
import time
import logging
import threading
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import fitz  # PyMuPDF

from app.config import settings
from app.documents.schemas import ChunkMetadata

logger = logging.getLogger("processor")


# ── Progress tracking ──────────────────────────────────────────────
_processing_status: Dict[int, Dict] = {}


def get_processing_status(doc_id: int) -> Optional[Dict]:
    return _processing_status.get(doc_id)


def _update_progress(doc_id: int, **kwargs):
    if doc_id not in _processing_status:
        _processing_status[doc_id] = {
            "status": "pending", "progress": 0, "total_pages": 0,
            "current_page": 0, "message": "Queued...", "started_at": time.time(),
        }
    _processing_status[doc_id].update(kwargs)


def _clear_progress(doc_id: int):
    if doc_id in _processing_status:
        _processing_status[doc_id]["status"] = "done"
        _processing_status[doc_id]["progress"] = 100


# ── OCR singleton with thread-safe init ────────────────────────────
_ocr_instance = None
_ocr_lock = threading.Lock()


def get_ocr():
    """Get or create OCR instance (thread-safe lazy singleton)."""
    global _ocr_instance
    if _ocr_instance is None:
        with _ocr_lock:
            # Double-check after acquiring lock
            if _ocr_instance is None:
                logger.info("Loading RapidOCR engine (one-time)...")
                from rapidocr_onnxruntime import RapidOCR
                _ocr_instance = RapidOCR()
                logger.info("RapidOCR loaded!")
    return _ocr_instance


# ── Text extraction helpers ────────────────────────────────────────

def extract_year_from_text(text: str) -> Optional[int]:
    for pattern in [r'\b(20[0-9]{2})\b', r'\b(19[0-9]{2})\b']:
        matches = re.findall(pattern, text)
        if matches:
            years = [int(y) for y in matches]
            current_year = datetime.now().year
            valid = [y for y in years if 1950 <= y <= current_year + 1]
            if valid:
                return max(valid)
    return None


def is_table_line(line: str) -> bool:
    if '|' in line:
        return True
    if line.count('\t') >= 2:
        return True
    if re.search(r'\s{3,}', line) and len(line.split()) >= 3:
        return True
    return False


def cluster_ocr_elements(elements: List[Dict], y_tolerance: float = 10) -> List[List[Dict]]:
    """Group OCR elements into lines based on Y-coordinate."""
    if not elements:
        return []
    sorted_elems = sorted(elements, key=lambda e: e['y1'])
    lines = []
    current_line = [sorted_elems[0]]
    current_y = sorted_elems[0]['y1']

    for elem in sorted_elems[1:]:
        if abs(elem['y1'] - current_y) <= y_tolerance:
            current_line.append(elem)
        else:
            current_line.sort(key=lambda e: e['x1'])
            lines.append(current_line)
            current_line = [elem]
            current_y = elem['y1']

    current_line.sort(key=lambda e: e['x1'])
    lines.append(current_line)
    return lines


# ── Native text extraction ─────────────────────────────────────────

def _try_native_text(page) -> Optional[str]:
    text = page.get_text("text")
    stripped = text.strip()
    if len(stripped) >= 50:
        return stripped
    return None


# ── OCR one page (thread pool) ─────────────────────────────────────

def _ocr_single_page(page_num: int, pdf_path: str, dpi: int = 150) -> Dict:
    """OCR a single page. Runs in thread pool, shares OCR engine."""
    import numpy as np

    pdf_doc = fitz.open(pdf_path)
    page = pdf_doc[page_num]
    page_w, page_h = page.rect.width, page.rect.height

    pix = page.get_pixmap(dpi=dpi)
    img_w, img_h = pix.width, pix.height

    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(img_h, img_w, pix.n)
    if pix.n == 4:
        img_array = img_array[:, :, :3]

    ocr = get_ocr()
    result, _ = ocr(img_array)

    pdf_doc.close()

    if not result:
        return {"page_num": page_num + 1, "text": "", "elements": []}

    elements = []
    for detection in result:
        bbox, text, confidence = detection[0], detection[1], detection[2]
        if confidence < 0.3:
            continue

        scale_x = page_w / img_w
        scale_y = page_h / img_h
        x1 = min(pt[0] for pt in bbox) * scale_x
        y1 = min(pt[1] for pt in bbox) * scale_y
        x2 = max(pt[0] for pt in bbox) * scale_x
        y2 = max(pt[1] for pt in bbox) * scale_y

        elements.append({
            'text': text,
            'x1': float(x1), 'y1': float(y1),
            'x2': float(x2), 'y2': float(y2),
            'confidence': float(confidence),
        })

    lines = cluster_ocr_elements(elements)
    page_text = "\n".join(" ".join(e['text'] for e in line) for line in lines)

    return {
        "page_num": page_num + 1,
        "text": page_text,
        "elements": elements,
    }


# ── OCR cache (saves results so pdf_to_word doesn't re-OCR) ───────

def _save_ocr_cache(pdf_path: str, pages_data: list):
    """Save OCR results to cache file for reuse by pdf_to_word."""
    cache_path = Path(pdf_path).parent / f"{Path(pdf_path).stem}_ocr_cache.json"
    cache = []
    for pd in pages_data:
        if pd is None:
            cache.append(None)
            continue
        cache.append({
            "page_num": pd.get("page_num"),
            "text": pd.get("text", ""),
            "elements": pd.get("elements", []),
            "is_native": len(pd.get("elements", [])) == 0,
        })
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)
    logger.info("  OCR cache saved for pdf_to_word reuse")


# ── Main extraction function ───────────────────────────────────────

def extract_text_from_pdf(
    pdf_path: str,
    doc_id: int = 0,
    dpi: int = 150,
    max_workers: int = 8,
) -> Tuple[str, List[Dict]]:
    """
    Extract text from PDF — FAST.
    
    Strategy:
    1. Try native text (instant)
    2. Parallel OCR for scanned pages at 150 DPI
    3. Save OCR cache for pdf_to_word reuse
    """
    _update_progress(doc_id, status="extracting", message="Opening PDF...")

    pdf_doc = fitz.open(pdf_path)
    total_pages = len(pdf_doc)
    _update_progress(doc_id, total_pages=total_pages, message=f"Analyzing {total_pages} pages...")

    pages_data = [None] * total_pages
    pages_needing_ocr = []

    # Phase 1: Native text (instant)
    for page_num in range(total_pages):
        page = pdf_doc[page_num]
        native_text = _try_native_text(page)
        if native_text is not None:
            pages_data[page_num] = {
                "page_num": page_num + 1,
                "text": native_text,
                "elements": [],
            }
            _update_progress(
                doc_id,
                current_page=page_num + 1,
                progress=int((page_num + 1) / total_pages * 30),
                message=f"Page {page_num + 1}/{total_pages}: Native text",
            )
        else:
            pages_needing_ocr.append(page_num)

    pdf_doc.close()

    # Phase 2: Parallel OCR for scanned pages
    if pages_needing_ocr:
        ocr_count = len(pages_needing_ocr)
        _update_progress(doc_id, message=f"OCR on {ocr_count} scanned pages...", progress=30)

        # Pre-warm OCR engine before spawning threads (avoids race condition)
        get_ocr()

        completed = 0
        with ThreadPoolExecutor(max_workers=min(max_workers, ocr_count)) as executor:
            futures = {
                executor.submit(_ocr_single_page, pn, pdf_path, dpi): pn
                for pn in pages_needing_ocr
            }
            for future in as_completed(futures):
                page_num = futures[future]
                try:
                    result = future.result()
                    pages_data[page_num] = result
                except Exception as e:
                    logger.error("OCR Error page %d: %s", page_num + 1, e)
                    pages_data[page_num] = {"page_num": page_num + 1, "text": "", "elements": []}

                completed += 1
                pct = 30 + int(completed / ocr_count * 50)
                _update_progress(doc_id, current_page=page_num + 1, progress=pct,
                                 message=f"OCR: {completed}/{ocr_count} pages done")
    else:
        _update_progress(doc_id, progress=80, message="All pages native (no OCR needed)")

    # Stitch text in page order
    full_text = "\n\n".join(
        pd["text"] for pd in pages_data if pd and pd.get("text")
    )

    # Save OCR cache so pdf_to_word can reuse it (no double OCR!)
    valid_pages = [pd for pd in pages_data if pd is not None]
    _save_ocr_cache(pdf_path, valid_pages)

    _update_progress(doc_id, progress=85, message="Text extraction complete")
    return full_text.strip(), valid_pages


# ── Smart chunking ──────────────────────────────────────────────────

def smart_chunk_text(
    text: str,
    page_num: int,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> List[Tuple[str, str]]:
    """Smart chunking that keeps tables intact."""
    chunks = []
    lines = text.split('\n')

    current_chunk = []
    current_size = 0
    in_table = False
    table_buffer = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        is_table = is_table_line(line)

        if is_table:
            if current_chunk and not in_table:
                chunk_text = ' '.join(current_chunk)
                if chunk_text:
                    chunks.append((chunk_text, "text"))
                current_chunk = []
                current_size = 0
            table_buffer.append(line)
            in_table = True
        else:
            if in_table and table_buffer:
                table_text = '\n'.join(table_buffer)
                chunks.append((table_text, "table"))
                table_buffer = []
                in_table = False

            line_size = len(line)
            if current_size + line_size > chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append((chunk_text, "text"))
                overlap_text = chunk_text[-chunk_overlap:] if len(chunk_text) > chunk_overlap else ""
                current_chunk = [overlap_text] if overlap_text else []
                current_size = len(overlap_text)

            current_chunk.append(line)
            current_size += line_size + 1

    if table_buffer:
        chunks.append(('\n'.join(table_buffer), "table"))
    elif current_chunk:
        chunk_text = ' '.join(current_chunk)
        if chunk_text:
            chunks.append((chunk_text, "text"))

    return chunks


# ── Main entry point ───────────────────────────────────────────────

def process_document(
    pdf_path: str,
    user_id: int,
    doc_id: int,
    doc_type: str,
    filename: str,
) -> Tuple[str, List[Dict], Optional[int]]:
    """Process a PDF: extract text, chunk, return metadata."""
    logger.info("="*60)
    logger.info("PROCESSING DOCUMENT %s", filename)
    logger.info("  Doc ID: %s | Type: %s | User: %s", doc_id, doc_type.upper(), user_id)
    logger.info("="*60)

    _update_progress(doc_id, status="processing", message="Starting...")
    start = time.time()

    full_text, pages_data = extract_text_from_pdf(pdf_path, doc_id=doc_id)

    extract_time = time.time() - start
    logger.info("  Text extraction: %.1fs | Pages: %d | Chars: %d",
                extract_time, len(pages_data), len(full_text))

    year = extract_year_from_text(full_text)

    _update_progress(doc_id, progress=90, message="Chunking and indexing...")

    all_chunks = []
    chunk_index = 0

    for page_data in pages_data:
        page_num = page_data["page_num"]
        page_text = page_data.get("text", "")
        if not page_text:
            continue

        chunks = smart_chunk_text(
            page_text, page_num,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        for chunk_text, chunk_type in chunks:
            all_chunks.append({
                "content": chunk_text,
                "metadata": {
                    "user_id": user_id, "doc_id": doc_id, "doc_type": doc_type,
                    "filename": filename, "year": year, "page_num": page_num,
                    "chunk_type": chunk_type, "chunk_index": chunk_index,
                },
            })
            chunk_index += 1

    logger.info("  Chunking: %d chunks created", len(all_chunks))
    return full_text, all_chunks, year
