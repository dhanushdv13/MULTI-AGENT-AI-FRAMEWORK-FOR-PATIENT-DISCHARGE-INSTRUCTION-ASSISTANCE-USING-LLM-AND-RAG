"""
Base Agent - Common functionality for all agents (VectorID Scoped).
"""
from typing import List, Dict, Optional, Any
from app.core.config import LLM_MODEL, GOOGLE_API_KEY, LLM_TEMPERATURE

def get_llm(temperature: float = None):
    """Get the LLM instance."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=temperature if temperature is not None else LLM_TEMPERATURE,
        convert_system_message_to_human=True,
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
    
    def __init__(self, vector_id: str):
        self.vector_id = vector_id
        self.llm = get_llm()
    
    async def search_current_document_async(self, query: str, k: int = 5, doc_type: Optional[str] = None) -> List[Dict]:
        """Search the current document (scoped by vector_id) asynchronously."""
        from app.ai.vectorstore.store import search_document_async
        return await search_document_async(self.vector_id, query, k, doc_type=doc_type)

    def search_current_document(self, query: str, k: int = 5, doc_type: Optional[str] = None) -> List[Dict]:
        """Search the current document (scoped by vector_id)."""
        from app.ai.vectorstore.store import search_document
        return search_document(self.vector_id, query, k, doc_type=doc_type)

    # Async method aliases
    async def search_discharge_async(self, query: str, k: int = 5) -> List[Dict]:
        """Search discharge content in current document (Async)."""
        return await self.search_current_document_async(query, k, doc_type="discharge")
    
    async def search_bills_async(self, query: str, k: int = 5) -> List[Dict]:
        """Search bill content in current document (Async)."""
        return await self.search_current_document_async(query, k, doc_type="bill")
    
    async def search_regulations_async(self, query: str, k: int = 5) -> List[Dict]:
        """Search shared regulations (NPPA, CGHS) (Async)."""
        from app.ai.vectorstore.store import get_regulations_store
        store = get_regulations_store()
        return await store.search_async(query, k)
    
    async def search_dietary_async(self, query: str, k: int = 5) -> List[Dict]:
        """Search shared dietary guidelines (Async)."""
        from app.ai.vectorstore.store import get_dietary_store
        store = get_dietary_store()
        return await store.search_async(query, k)

    async def search_insurance_async(self, query: str, k: int = 5) -> List[Dict]:
        """Search shared insurance policies (Async)."""
        from app.ai.vectorstore.store import get_insurance_store
        store = get_insurance_store()
        return await store.search_async(query, k)

    # Legacy method aliases for compatibility
    def search_discharge(self, query: str, k: int = 5) -> List[Dict]:
        """Search discharge content in current document."""
        return self.search_current_document(query, k, doc_type="discharge")
    
    def search_bills(self, query: str, k: int = 5) -> List[Dict]:
        """Search bill content in current document."""
        return self.search_current_document(query, k, doc_type="bill")
    
    def search_regulations(self, query: str, k: int = 5) -> List[Dict]:
        """Search shared regulations (NPPA, CGHS)."""
        from app.ai.vectorstore.store import get_regulations_store
        return get_regulations_store().search(query, k)
    
    def search_dietary(self, query: str, k: int = 5) -> List[Dict]:
        """Search shared dietary guidelines."""
        from app.ai.vectorstore.store import get_dietary_store
        return get_dietary_store().search(query, k)

    def search_insurance(self, query: str, k: int = 5) -> List[Dict]:
        """Search shared insurance policies."""
        from app.ai.vectorstore.store import get_insurance_store
        return get_insurance_store().search(query, k)
    
    async def ask_llm_async(self, prompt: str) -> str:
        """Send a prompt to the LLM and get response asynchronously."""
        response = await self.llm.ainvoke(prompt)
        return response.content

    def ask_llm(self, prompt: str) -> str:
        """Send a prompt to the LLM and get response (Synchronous)."""
        response = self.llm.invoke(prompt)
        return response.content
