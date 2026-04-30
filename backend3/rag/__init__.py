"""
RAG (Retrieval Augmented Generation) module.

This module provides functionality for:
- PDF processing and text extraction
- Embedding generation using HuggingFace models
- Vector storage and retrieval using FAISS
"""

from rag.pdf_processor import PDFProcessor
from rag.embedding_manager import EmbeddingManager
from rag.vector_store import VectorStoreManager

embed_instance = EmbeddingManager()

__all__ = [
    'PDFProcessor',
    'EmbeddingManager',
    'VectorStoreManager'
]
