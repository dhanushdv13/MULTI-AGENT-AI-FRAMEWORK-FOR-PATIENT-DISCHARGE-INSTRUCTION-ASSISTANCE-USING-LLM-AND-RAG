"""
Script to build FAISS vector stores from PDF documents in diet_docs directory.

This script:
1. Loads all PDFs from the diet_docs directory
2. Extracts and chunks the text
3. Generates embeddings using HuggingFace model (all-MiniLM-L6-v2)
4. Creates and saves FAISS vector stores
"""

import os
from pathlib import Path
from rag.pdf_processor import PDFProcessor
from rag.embedding_manager import EmbeddingManager
from rag.vector_store import VectorStoreManager


def build_diet_vector_store():
    """Build vector store for diet documents."""
    
    # Paths
    base_dir = Path(__file__).parent
    diet_docs_dir = base_dir / "shared" / "diet_docs"
    vector_store_path = base_dir / "vectorstores" / "diet_docs"
    
    print("=" * 60)
    print("Building Diet Documents Vector Store")
    print("=" * 60)
    print(f"\nSource Directory: {diet_docs_dir}")
    print(f"Vector Store Path: {vector_store_path}")
    
    # Step 1: Process PDFs
    print("\n[1/3] Processing PDF documents...")
    processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
    
    try:
        chunks = processor.process_directory(str(diet_docs_dir))
        
        if not chunks:
            print("ERROR: No documents were processed. Check if PDFs exist in the directory.")
            return False
        
        print(f"✓ Successfully processed {len(chunks)} chunks")
        
    except Exception as e:
        print(f"ERROR processing PDFs: {e}")
        return False
    
    # Step 2: Initialize embeddings
    print("\n[2/3] Initializing embeddings...")
    try:
        embedding_manager = EmbeddingManager()
        print("✓ Embeddings initialized")
    except Exception as e:
        print(f"ERROR initializing embeddings: {e}")
        return False
    
    # Step 3: Create and save vector store
    print("\n[3/3] Creating and saving vector store...")
    try:
        store_manager = VectorStoreManager(
            embedding_manager,
            store_path=str(vector_store_path)
        )
        
        store_manager.create_vector_store(chunks)
        store_manager.save_vector_store()
        
        print("✓ Vector store created and saved")
        
    except Exception as e:
        print(f"ERROR creating vector store: {e}")
        return False
    
    # Test the vector store
    print("\n" + "=" * 60)
    print("Testing Vector Store")
    print("=" * 60)
    
    test_queries = [
        "What are the dietary recommendations for diabetes?",
        "How much protein should I consume?",
        "What foods should I avoid?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            results = store_manager.similarity_search(query, k=2)
            print(f"Found {len(results)} results")
            
            if results:
                doc = results[0]
                print(f"  Top result from: {doc.metadata.get('source', 'Unknown')}")
                print(f"  Preview: {doc.page_content[:150]}...")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Vector store build completed successfully!")
    print("=" * 60)
    print(f"\nVector store saved at: {vector_store_path}")
    print("\nYou can now use this vector store in your application.")
    
    return True


def main():
    """Main function."""
    success = build_diet_vector_store()
    
    if not success:
        print("\n❌ Vector store build failed. Please check the errors above.")
        exit(1)
    else:
        print("\n✅ All done!")


if __name__ == "__main__":
    main()
