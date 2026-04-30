"""
Vector Stores module - Provides pre-loaded FAISS vector stores for the application.

This module loads and exposes vector stores that can be imported and used
throughout the application.
"""

import os
from pathlib import Path
from rag.embedding_manager import EmbeddingManager
from rag.vector_store import VectorStoreManager


# Initialize embedding manager
embedding_manager = EmbeddingManager()

# Base paths
BASE_DIR = Path(__file__).parent
VECTOR_STORES_DIR = BASE_DIR / "vectorstores"

# Initialize vector store managers
diet_docs_path = VECTOR_STORES_DIR / "diet_docs"
discharge_path = VECTOR_STORES_DIR / "discharge"

# Load diet documents vector store
print("Loading diet documents vector store...")
diet_store_manager = VectorStoreManager(embedding_manager, store_path=str(diet_docs_path))

try:
    if diet_docs_path.exists():
        diet_kb1 = diet_store_manager.load_vector_store()
        diet_kb2 = diet_kb1  # Using the same store for both kb1 and kb2
        print("✓ Diet documents vector store loaded successfully")
    else:
        print(f"⚠ Warning: Diet vector store not found at {diet_docs_path}")
        print("Please run 'python build_vector_stores.py' to create the vector stores")
        diet_kb1 = None
        diet_kb2 = None
except Exception as e:
    print(f"⚠ Warning: Failed to load diet vector store: {e}")
    diet_kb1 = None
    diet_kb2 = None

# Load discharge summary vector store (placeholder for now)
print("Loading discharge summary vector store...")
discharge_store_manager = VectorStoreManager(embedding_manager, store_path=str(discharge_path))

try:
    if discharge_path.exists():
        discharge_kb = discharge_store_manager.load_vector_store()
        print("✓ Discharge summary vector store loaded successfully")
    else:
        print(f"⚠ Warning: Discharge vector store not found at {discharge_path}")
        print("You can create it using the same approach as diet_docs")
        discharge_kb = None
except Exception as e:
    print(f"⚠ Warning: Failed to load discharge vector store: {e}")
    discharge_kb = None


# Export vector stores
__all__ = ['diet_kb1', 'diet_kb2', 'discharge_kb', 'embedding_manager']
