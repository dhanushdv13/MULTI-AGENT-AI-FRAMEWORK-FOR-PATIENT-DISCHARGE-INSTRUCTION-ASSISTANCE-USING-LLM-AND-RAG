"""
Document Processor — Handles PDF extraction, OCR, and Chunking.

Adapted for Backend Integration:
- Removes SQLAlchemy dependencies.
- Returns data directly to caller for MongoDB storage.
- Uses `vector_id` instead of `user_id` for metadata.
"""
import os
import re
import json
import logging
import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from app.core import config
from app.ai.documents import ChunkMetadata

# Configure logging
logger = logging.getLogger("processor")

# ══════════════════════════════════════════════════════════════════════
# OCR & Text Extraction Logic
# ══════════════════════════════════════════════════════════════════════

def extract_text_from_pdf(pdf_path: str) -> Tuple[str, List[Dict]]:
    """
    Extract text from PDF using Hybrid approach (Native + OCR).
    
    Returns:
        full_text: Combined text of all pages
        pages_data: List of dicts with 'text', 'tables', 'elements' (for cache)
    """
    doc = fitz.open(pdf_path)
    full_text = []
    pages_data = []
    
    # Initialize RapidOCR only if needed (lazy load)
    ocr_engine = None
    
    for page_num, page in enumerate(doc):
        # 1. Try Native Extraction
        text = page.get_text()
        
        # Heuristic: If page has very little text, it might be scanned
        if len(text.strip()) < 50:
            logger.info(f"Page {page_num+1} seems scanned. Running OCR...")
            
            if ocr_engine is None:
                from rapidocr_onnxruntime import RapidOCR
                ocr_engine = RapidOCR()
            
            # Get image of page
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            
            # Run OCR
            result, _ = ocr_engine(img_bytes)
            
            if result:
                # Combine text from OCR results
                ocr_text = "\n".join([line[1] for line in result])
                
                # Format elements for cache (compatible with pdf_to_word.py)
                elements = []
                for line in result:
                    box, txt, conf = line
                    # Convert box points to x1, y1, x2, y2
                    # RapidOCR returns [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                    x_coords = [p[0] for p in box]
                    y_coords = [p[1] for p in box]
                    elements.append({
                        "text": txt,
                        "x1": min(x_coords),
                        "y1": min(y_coords),
                        "x2": max(x_coords),
                        "y2": max(y_coords),
                        "conf": float(conf)
                    })
                
                text = ocr_text
                pages_data.append({
                    "text": text,
                    "is_native": False,
                    "elements": elements
                })
            else:
                pages_data.append({"text": "", "is_native": False, "elements": []})
        else:
            # Native page
            pages_data.append({
                "text": text,
                "is_native": True,
                "elements": [] # Native pages don't need elements for basic cache
            })
        
        full_text.append(text)
    
    return "\n".join(full_text), pages_data


def save_ocr_cache(pages_data: List[Dict], output_path: str):
    """Save OCR results to a JSON file."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(pages_data, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save OCR cache: {e}")


# ══════════════════════════════════════════════════════════════════════
# Smart Chunking Logic
# ══════════════════════════════════════════════════════════════════════

def smart_chunking(text: str, max_chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Chunk text while preserving semantic boundaries (paragraphs, headers).
    """
    chunks = []
    
    # Split by double newlines (paragraphs)
    paragraphs = re.split(r'\n\s*\n', text)
    
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # If adding para exceeds max size, save current chunk and start new
        if len(current_chunk) + len(para) > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                # Keep overlap from end of previous chunk
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + "\n\n" + para
            else:
                # Para itself is too big, just add it (or split it further if strict)
                chunks.append(para)
                current_chunk = ""
        else:
            if current_chunk:
                current_chunk += "\n\n"
            current_chunk += para
            
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks


# ══════════════════════════════════════════════════════════════════════
# Main Processing Function
# ══════════════════════════════════════════════════════════════════════

async def process_document(
    pdf_path: str,
    user_id: str,
    upload_id: str,
    vector_id: str,
    doc_type: str = "discharge",
    original_filename: str = "",
    ocr_cache_path: Optional[str] = None
) -> Tuple[str, List[Dict], Optional[int], int]:
    """
    Process a PDF document: Extract Text -> Chunk -> Metadata.
    
    Args:
        pdf_path: Path to PDF file
        user_id: User ID string
        upload_id: Upload ID string (replaces doc_id)
        vector_id: Unique Vector ID string
        doc_type: Type of document
        original_filename: Original filename
        ocr_cache_path: Optional path to save OCR JSON cache
        
    Returns:
        full_text: Extracted text
        chunks_with_metadata: List of chunks with metadata
        year: Detected year (if any)
    """
    logger.info(f"Processing document {upload_id} ({original_filename}) for vector_id {vector_id}")
    
    try:
        # 1. Extract Text (CPU Bound - Run in Threadpool)
        from starlette.concurrency import run_in_threadpool
        full_text, pages_data = await run_in_threadpool(extract_text_from_pdf, pdf_path)
        
        # 2. Save OCR Cache (for PDF->Word conversion)
        # Determine path if not provided
        if not ocr_cache_path:
            ocr_cache_path = str(Path(pdf_path).parent / f"{Path(pdf_path).stem}_ocr_cache.json")
            
        await run_in_threadpool(save_ocr_cache, pages_data, ocr_cache_path)
        
        # 3. Detect Year (Simple heuristic)
        year = None
        year_match = re.search(r'\b(20\d{2})\b', full_text)
        if year_match:
            year = int(year_match.group(1))
            
        # 4. Create Chunks (CPU Bound regex)
        text_chunks = await run_in_threadpool(smart_chunking, full_text)
        
        # 5. Prepare Chunks with Metadata
        chunks_with_metadata = []
        for i, content in enumerate(text_chunks):
            # Try to find page number (approximate)
            # This is hard with just text chunks, so defaults to 1 or we map back if needed
            # For now, simplistic approach
            
            meta = ChunkMetadata(
                user_id=user_id,
                upload_id=upload_id,
                vector_id=vector_id,
                doc_type=doc_type,
                filename=original_filename,
                year=year,
                page_num=1, # TODO: Map back to actual page
                chunk_type="text",
                chunk_index=i
            )
            
            chunks_with_metadata.append({
                "content": content,
                "metadata": meta.model_dump()
            })
            
        logger.info(f"Generated {len(chunks_with_metadata)} chunks for {upload_id}")
        
        page_count = len(pages_data)
        return full_text, chunks_with_metadata, year, page_count
        
    except Exception as e:
        logger.error(f"Error processing document {upload_id}: {e}")
        raise e
