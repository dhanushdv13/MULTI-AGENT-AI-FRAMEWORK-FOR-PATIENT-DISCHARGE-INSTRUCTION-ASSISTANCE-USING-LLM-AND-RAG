"""
Embeddings Module - HuggingFace all-MiniLM-L6-v2 (LAZY LOADED)

The model is NOT loaded on import. It loads on first use.
This makes server startup instant (~2s instead of ~60s).
"""
import logging
from typing import List

from app.core import config

logger = logging.getLogger("embeddings")

# Lazy singleton - NOT loaded on import
_embedding_model = None


def get_embedding_model():
    """Get or create embedding model (lazy singleton). Loads on first call only."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model (first use, one-time ~30s)...")
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        logger.info("Embedding model loaded!")
    return _embedding_model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts (Synchronous)."""
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.tolist()


async def embed_texts_async(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts (Async/Threadpool)."""
    from starlette.concurrency import run_in_threadpool
    return await run_in_threadpool(embed_texts, texts)


def embed_query(query: str) -> List[float]:
    """Embed a single query (Synchronous)."""
    model = get_embedding_model()
    embedding = model.encode([query], convert_to_numpy=True, show_progress_bar=False)
    return embedding[0].tolist()


async def embed_query_async(query: str) -> List[float]:
    """Embed a single query (Async/Threadpool)."""
    from starlette.concurrency import run_in_threadpool
    return await run_in_threadpool(embed_query, query)


# Fixed dimension for all-MiniLM-L6-v2 = 384
# Hardcode to avoid loading the model just to get dimension
_EMBEDDING_DIM = 384


def get_embedding_dimension() -> int:
    """Get the embedding dimension for FAISS index. Hardcoded to avoid eager model load."""
    return _EMBEDDING_DIM
