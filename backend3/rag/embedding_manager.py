"""
Embedding Manager for generating and managing embeddings using HuggingFace models.
"""
import os
from typing import List
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()


class EmbeddingManager:
    """Manages embeddings using HuggingFace models."""
    
    def __init__(self, model_name: str = None):
        """
        Initialize embedding manager.
        
        Args:
            model_name: Name of HuggingFace model. If None, reads from .env
        """
        if model_name is None:
            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        self.model_name = model_name
        print(f"Initializing embeddings with model: {model_name}")
        
        # Initialize HuggingFace embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},  # Use 'cuda' if GPU available
            encode_kwargs={'normalize_embeddings': True}
        )
        
        print("Embeddings initialized successfully")
    
    def get_embeddings(self):
        """
        Get the embeddings object.
        
        Returns:
            HuggingFaceEmbeddings object
        """
        return self.embeddings
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query.
        
        Args:
            text: Query text
            
        Returns:
            Embedding vector
        """
        return self.embeddings.embed_query(text)


if __name__ == "__main__":
    # Test the embedding manager
    manager = EmbeddingManager()
    
    # Test with sample text
    sample_texts = [
        "What are the dietary recommendations for diabetes?",
        "How much protein should I consume daily?"
    ]
    
    print("\nGenerating embeddings for sample texts...")
    embeddings = manager.embed_documents(sample_texts)
    
    print(f"Generated {len(embeddings)} embeddings")
    print(f"Embedding dimension: {len(embeddings[0])}")
    
    # Test query embedding
    query = "diabetes diet"
    query_embedding = manager.embed_query(query)
    print(f"\nQuery embedding dimension: {len(query_embedding)}")
