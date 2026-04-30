"""
Base Agent - Common functionality for all agents
All heavy imports (LLM, vectorstore) are lazy — only loaded when agent is actually used.
"""
from typing import List, Dict, Optional, Any

from app.config import settings


def get_llm(temperature: float = None):
    """
    Get the configured LLM instance (lazy import).
    
    Uses gemini-2.5-flash model from Google Generative AI.
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )


def format_search_results(results: List[Dict], include_source: bool = True) -> str:
    """Format search results for LLM context."""
    if not results:
        return "No relevant documents found."
    
    formatted = []
    for i, r in enumerate(results, 1):
        text = f"[{i}] {r['content']}"
        if include_source and r.get('metadata'):
            meta = r['metadata']
            source = f"(Source: {meta.get('filename', 'unknown')}, Page {meta.get('page_num', '?')})"
            text += f"\n   {source}"
        formatted.append(text)
    
    return "\n\n".join(formatted)


class BaseAgent:
    """Base class for all agents with common RAG functionality."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.llm = get_llm()
    
    def search_discharge(self, query: str, k: int = 5) -> List[Dict]:
        """Search user's discharge documents."""
        from app.vectorstore.store import search_user_documents
        return search_user_documents(self.user_id, query, k, doc_type="discharge")
    
    def search_bills(self, query: str, k: int = 5) -> List[Dict]:
        """Search user's bill documents."""
        from app.vectorstore.store import search_user_documents
        return search_user_documents(self.user_id, query, k, doc_type="bill")
    
    def search_all_user_docs(self, query: str, k: int = 5) -> List[Dict]:
        """Search all user documents."""
        from app.vectorstore.store import search_user_documents
        return search_user_documents(self.user_id, query, k)
    
    def search_regulations(self, query: str, k: int = 5) -> List[Dict]:
        """Search shared regulations (NPPA, CGHS)."""
        from app.vectorstore.store import get_regulations_store
        return get_regulations_store().search(query, k)
    
    def search_dietary(self, query: str, k: int = 5) -> List[Dict]:
        """Search shared dietary guidelines."""
        from app.vectorstore.store import get_dietary_store
        return get_dietary_store().search(query, k)
    
    def ask_llm(self, prompt: str) -> str:
        """Send a prompt to the LLM and get response."""
        response = self.llm.invoke(prompt)
        return response.content
