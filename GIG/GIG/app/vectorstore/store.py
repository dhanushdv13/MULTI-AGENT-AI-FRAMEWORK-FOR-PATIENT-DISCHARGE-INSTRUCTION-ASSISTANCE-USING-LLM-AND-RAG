"""
FAISS Vector Store Management - Per-user indices with metadata filtering.

Key optimization: delete_document uses index.reconstruct_n() to extract
existing embeddings from FAISS — no embedding model load needed for delete.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
import faiss
import numpy as np

from app.config import settings
from app.vectorstore.embeddings import embed_texts, embed_query, get_embedding_dimension

logger = logging.getLogger("vectorstore")


class UserVectorStore:
    """
    Per-user FAISS vector store with metadata support.
    
    Structure:
    - FAISS index file: faiss_index/index.faiss
    - Metadata file: faiss_index/metadata.json
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.index_dir = settings.USERS_DIR / str(user_id) / "faiss_index"
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
        """
        Add document chunks to the index.
        
        Each chunk should have:
        - content: str
        - metadata: dict with user_id, doc_id, doc_type, filename, year, page_num, chunk_type, chunk_index
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
    
    def search(
        self,
        query: str,
        k: int = 5,
        doc_type: Optional[str] = None,
        year: Optional[int] = None,
        filename: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search the index with optional metadata filtering.
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
            
            # Apply filters
            if doc_type and meta.get('doc_type') != doc_type:
                continue
            if year and meta.get('year') != year:
                continue
            if filename and filename.lower() not in meta.get('filename', '').lower():
                continue
            
            results.append({
                'content': meta.get('content', ''),
                'metadata': {k: v for k, v in meta.items() if k != 'content'},
                'score': float(distances[0][i]),
            })
            
            if len(results) >= k:
                break
        
        return results
    
    def delete_document(self, doc_id: int):
        """
        Delete all chunks for a document.
        
        FAST: Extracts existing embeddings from FAISS using reconstruct_n()
        so we never need to reload the embedding model just for deletion.
        """
        # Find indices to KEEP (everything except this doc_id)
        keep_indices = [
            i for i, m in enumerate(self.metadata)
            if m.get('doc_id') != doc_id
        ]
        
        if len(keep_indices) == len(self.metadata):
            return  # Nothing to delete
        
        removed = len(self.metadata) - len(keep_indices)
        
        if keep_indices and self.index.ntotal > 0:
            # Extract existing embeddings from FAISS (no model needed!)
            all_vectors = self.index.reconstruct_n(0, self.index.ntotal)
            
            # Keep only vectors for non-deleted docs
            kept_vectors = all_vectors[keep_indices]
            kept_metadata = [self.metadata[i] for i in keep_indices]
            
            # Rebuild index
            dim = self.index.d
            self.index = faiss.IndexFlatL2(dim)
            self.index.add(kept_vectors)
            self.metadata = kept_metadata
        else:
            # All documents deleted — empty index
            dim = get_embedding_dimension()
            self.index = faiss.IndexFlatL2(dim)
            self.metadata = []
        
        self.save()
        logger.info("Removed %d vectors for doc_id=%d (%d remaining)", removed, doc_id, len(self.metadata))


# Cache for user vector stores
_user_stores: Dict[int, UserVectorStore] = {}


def get_user_store(user_id: int) -> UserVectorStore:
    """Get or create a user's vector store."""
    if user_id not in _user_stores:
        _user_stores[user_id] = UserVectorStore(user_id)
    return _user_stores[user_id]


def add_document_to_index(user_id: int, chunks: List[Dict]):
    """Add document chunks to a user's index."""
    store = get_user_store(user_id)
    store.add_documents(chunks)


def search_user_documents(
    user_id: int,
    query: str,
    k: int = 5,
    doc_type: Optional[str] = None,
    year: Optional[int] = None,
    filename: Optional[str] = None,
) -> List[Dict]:
    """Search a user's documents."""
    store = get_user_store(user_id)
    return store.search(query, k, doc_type, year, filename)


# ============================================================================
# Shared Vector Stores (Regulations, Dietary Guidelines)
# ============================================================================

class SharedVectorStore:
    """Shared vector store for regulations and dietary guidelines."""
    
    def __init__(self, name: str):
        self.name = name
        self.index_dir = settings.SHARED_DIR / f"{name}_index"
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


# Lazy singletons for shared stores — only created when first accessed
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
