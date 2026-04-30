from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, PlainTextResponse
from datetime import datetime
import uuid
import os
import shutil
import time
from starlette.concurrency import run_in_threadpool

from app.db.mongo import uploads
from app.core.deps import current_user

# AI Imports (Moved to top level for background task visibility, assuming no circular deps)
from app.ai.processor import process_document
from app.ai.pdf_to_word import pdf_to_word
from app.ai.vectorstore.store import add_document_to_index_async

router = APIRouter(prefix="/uploads", tags=["Uploads"])

async def process_upload_background(
    upload_id: str,
    user_id: str,
    file_path: str,
    vector_id: str,
    original_filename: str,
    extracted_path: str,
    ocr_cache_path: str
):
    try:
        # Step 1: Extract Text & Chunk
        await uploads.update_one(
            {"_id": upload_id}, 
            {"$set": {"processing_step": "Extracting text and structure...", "vector_status": "PROCESSING"}}
        )
        
        full_text, chunks, year, page_count = await process_document(
            pdf_path=file_path,
            user_id=user_id,
            upload_id=upload_id,
            vector_id=vector_id,
            doc_type="discharge",
            original_filename=original_filename,
            ocr_cache_path=ocr_cache_path
        )
        
        # Step 2: Indexing
        await uploads.update_one(
            {"_id": upload_id}, 
            {"$set": {"processing_step": f"Generating embeddings for {page_count} pages...", "page_count": page_count}}
        )
        
        await add_document_to_index_async(vector_id, chunks)
        
        # Step 3: Word Generation
        await uploads.update_one(
            {"_id": upload_id}, 
            {"$set": {"processing_step": "Generating Word document..."}}
        )
        
        await run_in_threadpool(
            pdf_to_word, 
            input_pdf=file_path, 
            output_docx=extracted_path,
            ocr_json_path=ocr_cache_path
        )
        
        # Completion
        await uploads.update_one(
            {"_id": upload_id}, 
            {
                "$set": {
                    "vector_status": "COMPLETED",
                    "processing_step": "Ready",
                    "extracted_content_path": extracted_path,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
    except Exception as e:
        print(f"Background Processing Failed: {e}")
        await uploads.update_one(
            {"_id": upload_id}, 
            {
                "$set": {
                    "vector_status": "FAILED",
                    "processing_step": f"Failed: {str(e)}",
                    "updated_at": datetime.utcnow()
                }
            }
        )

# -------------------------------
# POST /uploads/
# -------------------------------
@router.post("/")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: str | None = Form(None),
    additional_notes: str | None = Form(None),
    user=Depends(current_user)
):
    # Generate IDs
    upload_id = str(uuid.uuid4())
    vector_id = f"vec_{uuid.uuid4().hex}"

    upload_dir = "data/uploads"
    extracted_dir = "data/extracted_content"
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(extracted_dir, exist_ok=True)
    
    # Generate filenames
    timestamp = int(time.time())
    sanitized_filename = "".join(x for x in file.filename if x.isalnum() or x in "._-")
    user_id_str = str(user["_id"])
    
    file_base, file_ext = os.path.splitext(sanitized_filename)
    unique_base = f"{file_base}_{user_id_str}_{timestamp}"
    
    storage_filename = f"{unique_base}{file_ext}"
    file_path = f"{upload_dir}/{storage_filename}"
    
    extracted_filename = f"{unique_base}_extracted.docx"
    extracted_path = f"{extracted_dir}/{extracted_filename}"
    
    ocr_cache_filename = f"{unique_base}_ocr_cache.json"
    ocr_cache_path = f"{extracted_dir}/{ocr_cache_filename}"
    
    # Save file immediately
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Initial DB Insert
    doc = {
        "_id": upload_id,
        "user_id": user_id_str,
        "filename": file.filename,
        "description": description,
        "file_path": file_path,
        "extracted_content_path": None, # Will be set on completion
        "vector_status": "PROCESSING",
        "processing_step": "Queued",
        "vector_id": vector_id,
        "page_count": 0,
        "additional_notes": additional_notes,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await uploads.insert_one(doc)
    
    # Trigger Background Task
    background_tasks.add_task(
        process_upload_background,
        upload_id,
        user_id_str,
        file_path,
        vector_id,
        file.filename,
        extracted_path,
        ocr_cache_path
    )

    return {
        "upload_id": upload_id,
        "vector_id": vector_id,
        "vector_status": "PROCESSING",
        "message": "Upload started"
    }


# -------------------------------
# GET /uploads/   (all_files)
# -------------------------------
@router.get("/")
async def all_uploads(user=Depends(current_user)):
    docs = await uploads.find(
        {"user_id": str(user["_id"])}
    ).to_list(100)

    for d in docs:
        d["upload_id"] = str(d["_id"])
        d["_id"] = str(d["_id"])

    return docs


# -------------------------------
# GET /uploads/{upload_id}  (files/{id})
# -------------------------------
@router.get("/{upload_id}")
async def single_upload(upload_id: str, user=Depends(current_user)):
    doc = await uploads.find_one(
        {"_id": upload_id, "user_id": str(user["_id"])}
    )

    if not doc:
        raise HTTPException(status_code=404, detail="Upload not found")

    doc["upload_id"] = str(doc["_id"])
    doc["_id"] = str(doc["_id"])
    return doc


# -------------------------------
# GET /uploads/{upload_id}/content (Raw File)
# -------------------------------
@router.get("/{upload_id}/content")
async def get_upload_content(upload_id: str, user=Depends(current_user)):
    doc = await uploads.find_one(
        {"_id": upload_id, "user_id": str(user["_id"])}
    )

    if not doc or "file_path" not in doc:
        raise HTTPException(status_code=404, detail="File not found")

    import os
    if not os.path.exists(doc["file_path"]):
        raise HTTPException(status_code=404, detail="File on disk not found")

    return FileResponse(doc["file_path"], filename=doc["filename"])


# -------------------------------
# GET /uploads/{upload_id}/extracted (OCR Content)
# -------------------------------
@router.get("/{upload_id}/extracted")
async def get_upload_extracted(upload_id: str, user=Depends(current_user)):
    doc = await uploads.find_one(
        {"_id": upload_id, "user_id": str(user["_id"])}
    )

    if not doc:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    extracted_path = doc.get("extracted_content_path")
    
    if not extracted_path:
        raise HTTPException(status_code=404, detail="No extracted document available.")

    import os
    if not os.path.exists(extracted_path):
        raise HTTPException(status_code=404, detail="Extracted file missing on server.")
        
# -------------------------------
# GET /uploads/{upload_id}/extracted/html (Formatted HTML for Viewing)
# -------------------------------
@router.get("/{upload_id}/extracted/html")
async def get_upload_html(upload_id: str, user=Depends(current_user)):
    doc = await uploads.find_one(
        {"_id": upload_id, "user_id": str(user["_id"])}
    )

    if not doc:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    docx_path = doc.get("extracted_content_path")
    if not docx_path:
        # Fallback to text if docx not ready? No, explicit endpoint.
        raise HTTPException(status_code=404, detail="Extracted document not found")

    import os
    if not os.path.exists(docx_path):
        raise HTTPException(status_code=404, detail="File missing on server")

    try:
        import mammoth
        with open(docx_path, "rb") as docx_file:
            result = mammoth.convert_to_html(docx_file)
            html = result.value
            
            # Simple wrapper for styling
            full_html = f"""
            <div class="mammoth-content">
                {html}
            </div>
            """
            return PlainTextResponse(full_html, media_type="text/html")
    except ImportError:
        raise HTTPException(status_code=500, detail="HTML conversion library missing (mammoth)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {e}")

# ... (keep existing text endpoint if needed, but HTML is superior)
