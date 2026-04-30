"""
MongoDB CRUD for document records.
"""
from datetime import datetime
from fastapi import HTTPException, status
from database import documents_col


class DocumentService:

    async def create_record(self, doc_id, user_id, filename, vector_id, file_path, description=None):
        now = datetime.now()
        doc = {
            "doc_id": doc_id,
            "user_id": user_id,
            "filename": filename,
            "description": description,
            "vector_id": vector_id,
            "vector_status": "PROCESSING",
            "processing_step": "Queued",
            "page_count": 0,
            "file_path": file_path,
            "created_at": now,
            "updated_at": now,
        }
        await documents_col().insert_one(doc)
        return doc

    async def get_all(self, user_id: str) -> list[dict]:
        cursor = documents_col().find({"user_id": user_id}, {"_id": 0})
        docs = await cursor.to_list(length=200)
        for doc in docs:
            doc["upload_id"] = doc.get("doc_id", "")
        return docs

    async def get_one(self, doc_id: str, user_id: str) -> dict:
        doc = await documents_col().find_one({"doc_id": doc_id, "user_id": user_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found or access denied")
        doc["upload_id"] = doc.get("doc_id", "")
        return doc

    async def update_status(self, doc_id: str, vector_status: str, processing_step: str):
        await documents_col().update_one(
            {"doc_id": doc_id},
            {"$set": {"vector_status": vector_status, "processing_step": processing_step, "updated_at": datetime.now()}},
        )

    async def mark_completed(self, doc_id: str, page_count: int,
                              ocr_cache_path: str = None, extracted_text_path: str = None):
        update = {
            "vector_status": "COMPLETED",
            "processing_step": "Ready",
            "page_count": page_count,
            "updated_at": datetime.now(),
        }
        if ocr_cache_path:
            update["ocr_cache_path"] = ocr_cache_path
        if extracted_text_path:
            update["extracted_content_path"] = extracted_text_path
        await documents_col().update_one({"doc_id": doc_id}, {"$set": update})


    async def mark_failed(self, doc_id: str, error: str):
        await documents_col().update_one(
            {"doc_id": doc_id},
            {"$set": {"vector_status": "FAILED", "processing_step": f"Failed: {error}", "updated_at": datetime.now()}},
        )
