"""
FAISS Vector Store Management - Per-document indices (VectorID based).

Key distinction: Indexes are stored by `vector_id`, not `user_id`.
Structure: data/vectors/{vector_id}/faiss_index
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
import faiss
import numpy as np

from app.core import config
from app.ai.vectorstore.embeddings import embed_texts, embed_query, get_embedding_dimension

# Configure logging
logger = logging.getLogger("vectorstore")


class DocumentVectorStore:
    """
    Manages a distinct FAISS index for a specific document (User upload).
    Path: data/vectors/{vector_id}/
    """
    
    def __init__(self, vector_id: str):
        self.vector_id = vector_id
        vectors_base = getattr(config, "VECTORS_DIR", Path("data/vectors"))
        self.index_dir = vectors_base / vector_id / "faiss_index"
        self.index_path = self.index_dir / "index.faiss"
        self.metadata_path = self.index_dir / "metadata.json"
        
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.index = None
        self.metadata = []
        
        self._load_or_create()
    
    def _load_or_create(self):
        """Load existing index or create new one."""
        if self.index_path.exists() and self.metadata_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        else:
            dim = get_embedding_dimension()
            self.index = faiss.IndexFlatL2(dim)
            self.metadata = []
    
    def save(self):
        """Save index and metadata to disk."""
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    async def add_documents_async(self, chunks: List[Dict]):
        """
        Add document chunks to the index (Async).
        """
        if not chunks:
            return
        
        # Extract texts and metadata
        texts = [chunk['content'] for chunk in chunks]
        metas = [chunk['metadata'] for chunk in chunks]
        
        # Generate embeddings (Async)
        from app.ai.vectorstore.embeddings import embed_texts_async
        embeddings = await embed_texts_async(texts)
        embeddings_np = np.array(embeddings, dtype=np.float32)
        
        # Add to FAISS index (Threadpool)
        from starlette.concurrency import run_in_threadpool
        await run_in_threadpool(self.index.add, embeddings_np)
        
        # Store metadata (with content for retrieval)
        for i, meta in enumerate(metas):
            meta['content'] = texts[i]
            self.metadata.append(meta)
        
        # Save to disk (Threadpool)
        await run_in_threadpool(self.save)

    def add_documents(self, chunks: List[Dict]):
        """
        Add document chunks to the index.
        """
        if not chunks:
            return
        
        # Extract texts and metadata
        texts = [chunk['content'] for chunk in chunks]
        metas = [chunk['metadata'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = embed_texts(texts)
        embeddings_np = np.array(embeddings, dtype=np.float32)
        
        # Add to FAISS index
        self.index.add(embeddings_np)
        
        # Store metadata (with content for retrieval)
        for i, meta in enumerate(metas):
            meta['content'] = texts[i]
            self.metadata.append(meta)
        
        # Save to disk
        self.save()
    
    async def search_async(
        self,
        query: str,
        k: int = 5,
        doc_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Search the index (Async/Threadpool).
        """
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(self.search, query, k, doc_type)

    def search(
        self,
        query: str,
        k: int = 5,
        doc_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Search the index.
        """
        if self.index.ntotal == 0:
            return []
        
        query_embedding = np.array([embed_query(query)], dtype=np.float32)
        
        search_k = min(k * 5, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, search_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            
            meta = self.metadata[idx]
            
            # Apply filters (if document has mixed types, though likely homogeneous)
            if doc_type and meta.get('doc_type') != doc_type:
                continue
            
            results.append({
                'content': meta.get('content', ''),
                'metadata': {k: v for k, v in meta.items() if k != 'content'},
                'score': float(distances[0][i]),
            })
            
            if len(results) >= k:
                break
        
        return results


# Cache for document vector stores
_doc_stores: Dict[str, DocumentVectorStore] = {}


def get_document_store(vector_id: str) -> DocumentVectorStore:
    """Get or create a document's vector store."""
    if vector_id not in _doc_stores:
        _doc_stores[vector_id] = DocumentVectorStore(vector_id)
    return _doc_stores[vector_id]


async def add_document_to_index_async(vector_id: str, chunks: List[Dict]):
    """Add document chunks to a vector index (Async)."""
    store = get_document_store(vector_id)
    await store.add_documents_async(chunks)


def add_document_to_index(vector_id: str, chunks: List[Dict]):
    """Add document chunks to a vector index."""
    store = get_document_store(vector_id)
    store.add_documents(chunks)


async def search_document_async(
    vector_id: str,
    query: str,
    k: int = 5,
    doc_type: Optional[str] = None
) -> List[Dict]:
    """Search a specific document's index (Async)."""
    store = get_document_store(vector_id)
    return await store.search_async(query, k, doc_type)


def search_document(
    vector_id: str,
    query: str,
    k: int = 5,
    doc_type: Optional[str] = None
) -> List[Dict]:
    """Search a specific document's index."""
    store = get_document_store(vector_id)
    return store.search(query, k, doc_type)


# ============================================================================
# Shared Vector Stores (Regulations, Dietary Guidelines)
# ============================================================================

class SharedVectorStore:
    """
    Manages shared indices (Regulations, Diet, Insurance).
    """
    
    def __init__(self, index_name: str):
        self.index_name = index_name
        # Use config.SHARED_DIR (need to ensure this exists in config)
        shared_base = getattr(config, "SHARED_DIR", Path("data/shared"))
        self.index_dir = shared_base / f"{index_name}_index"
        self.index_path = self.index_dir / "index.faiss"
        self.metadata_path = self.index_dir / "metadata.json"
        
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.index = None
        self.metadata = []
        
        self._load_or_create()
    
    def _load_or_create(self):
        """Load existing index or create new one."""
        if self.index_path.exists() and self.metadata_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        else:
            dim = get_embedding_dimension()
            self.index = faiss.IndexFlatL2(dim)
            self.metadata = []
    
    def save(self):
        """Save index and metadata to disk."""
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def add_documents(self, chunks: List[Dict]):
        """Add document chunks to the index."""
        if not chunks:
            return
        
        texts = [chunk['content'] for chunk in chunks]
        metas = [chunk['metadata'] for chunk in chunks]
        
        embeddings = embed_texts(texts)
        embeddings_np = np.array(embeddings, dtype=np.float32)
        
        self.index.add(embeddings_np)
        
        for i, meta in enumerate(metas):
            meta['content'] = texts[i]
            self.metadata.append(meta)
        
        self.save()
    
    async def search_async(self, query: str, k: int = 5) -> List[Dict]:
        """Search the shared index (Async/Threadpool)."""
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(self.search, query, k)

    def search(self, query: str, k: int = 5) -> List[Dict]:
        """Search the shared index."""
        if self.index.ntotal == 0:
            return []
        
        query_embedding = np.array([embed_query(query)], dtype=np.float32)
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            
            meta = self.metadata[idx]
            results.append({
                'content': meta.get('content', ''),
                'metadata': {k: v for k, v in meta.items() if k != 'content'},
                'score': float(distances[0][i]),
            })
        
        return results
    
    def is_empty(self) -> bool:
        """Check if the index is empty."""
        return self.index.ntotal == 0


# Lazy singletons for shared stores
_regulations_store: Optional[SharedVectorStore] = None
_dietary_store: Optional[SharedVectorStore] = None
_insurance_store: Optional[SharedVectorStore] = None


def get_regulations_store() -> SharedVectorStore:
    """Get the shared regulations store (lazy)."""
    global _regulations_store
    if _regulations_store is None:
        _regulations_store = SharedVectorStore("regulations")
    return _regulations_store


def get_dietary_store() -> SharedVectorStore:
    """Get the shared dietary guidelines store (lazy)."""
    global _dietary_store
    if _dietary_store is None:
        _dietary_store = SharedVectorStore("dietary")
    return _dietary_store


def get_insurance_store() -> SharedVectorStore:
    """Get the shared insurance policies store (lazy)."""
    global _insurance_store
    if _insurance_store is None:
        _insurance_store = SharedVectorStore("insurance")
    return _insurance_store
