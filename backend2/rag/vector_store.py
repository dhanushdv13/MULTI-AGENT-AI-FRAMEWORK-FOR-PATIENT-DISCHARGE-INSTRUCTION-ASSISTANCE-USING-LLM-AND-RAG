"""
Vector Store Manager for FAISS-based storage and retrieval.
"""
import os
from pathlib import Path
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from rag.embedding_manager import EmbeddingManager


class VectorStoreManager:
    """Manages FAISS vector stores for document retrieval."""
    
    def __init__(self, embedding_manager: EmbeddingManager, store_path: str = None):
        """
        Initialize vector store manager.
        
        Args:
            embedding_manager: EmbeddingManager instance
            store_path: Path to save/load vector store
        """
        self.embedding_manager = embedding_manager
        self.embeddings = embedding_manager.get_embeddings()
        self.store_path = store_path
        self.vector_store = None
    
    def create_vector_store(self, documents: List[Document]) -> FAISS:
        """
        Create a new FAISS vector store from documents.
        
        Args:
            documents: List of Document objects
            
        Returns:
            FAISS vector store
        """
        if not documents:
            raise ValueError("Cannot create vector store from empty document list")
        
        print(f"Creating vector store from {len(documents)} documents...")
        
        self.vector_store = FAISS.from_documents(
            documents=documents,
            embedding=self.embeddings
        )
        
        print("Vector store created successfully")
        return self.vector_store
    
    def add_documents(self, documents: List[Document]):
        """
        Add documents to existing vector store.
        
        Args:
            documents: List of Document objects to add
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Create one first.")
        
        print(f"Adding {len(documents)} documents to vector store...")
        self.vector_store.add_documents(documents)
        print("Documents added successfully")
    
    def save_vector_store(self, path: str = None):
        """
        Save vector store to disk.
        
        Args:
            path: Path to save the vector store. Uses self.store_path if not provided
        """
        if self.vector_store is None:
            raise ValueError("No vector store to save")
        
        save_path = path or self.store_path
        if save_path is None:
            raise ValueError("No save path provided")
        
        # Create directory if it doesn't exist
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Saving vector store to {save_path}...")
        self.vector_store.save_local(save_path)
        print("Vector store saved successfully")
    
    def load_vector_store(self, path: str = None) -> FAISS:
        """
        Load vector store from disk.
        
        Args:
            path: Path to load the vector store from. Uses self.store_path if not provided
            
        Returns:
            Loaded FAISS vector store
        """
        load_path = path or self.store_path
        if load_path is None:
            raise ValueError("No load path provided")
        
        if not os.path.exists(load_path):
            raise ValueError(f"Vector store not found at {load_path}")
        
        print(f"Loading vector store from {load_path}...")
        self.vector_store = FAISS.load_local(
            load_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        print("Vector store loaded successfully")
        return self.vector_store
    
    def get_vector_store(self) -> Optional[FAISS]:
        """
        Get the current vector store.
        
        Returns:
            FAISS vector store or None
        """
        return self.vector_store
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized")
        
        return self.vector_store.similarity_search(query, k=k)
    
    def similarity_search_with_score(self, query: str, k: int = 4):
        """
        Search for similar documents with similarity scores.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized")
        
        return self.vector_store.similarity_search_with_score(query, k=k)


if __name__ == "__main__":
    # Test the vector store manager
    from rag.pdf_processor import PDFProcessor
    
    # Process PDFs
    processor = PDFProcessor()
    docs_dir = "/home/abhijith/Desktop/Git/ai-insurance-agent/backend2/docs/shared/diet_docs"
    chunks = processor.process_directory(docs_dir)
    
    if chunks:
        # Create embeddings and vector store
        embedding_manager = EmbeddingManager()
        store_manager = VectorStoreManager(
            embedding_manager,
            store_path="/home/abhijith/Desktop/Git/ai-insurance-agent/backend2/rag/vector_stores/diet_docs"
        )
        
        # Create and save vector store
        store_manager.create_vector_store(chunks)
        store_manager.save_vector_store()
        
        # Test search
        query = "What are the dietary recommendations for diabetes?"
        results = store_manager.similarity_search(query, k=3)
        
        print(f"\nSearch results for: '{query}'")
        for i, doc in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"Page: {doc.metadata.get('page', 'N/A')}")
            print(f"Content: {doc.page_content[:200]}...")
