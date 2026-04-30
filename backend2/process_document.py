"""
Simple script to process a document/directory and store as FAISS embeddings.

Usage:
    python process_document.py <source_path> <vectorstore_name>

Examples:
    # Process a single PDF
    python process_document.py path/to/document.pdf my_doc

    # Process a directory of PDFs
    python process_document.py path/to/documents/ my_docs
"""

import sys
from pathlib import Path
from rag.pdf_processor import PDFProcessor
from rag.embedding_manager import EmbeddingManager
from rag.vector_store import VectorStoreManager


def process_and_store(source_path: str, vectorstore_name: str):
    """
    Process document(s) and store as FAISS embeddings.
    
    Args:
        source_path: Path to PDF file or directory containing PDFs
        vectorstore_name: Name for the vectorstore (e.g., 'discharge', 'medical_records')
    """
    # Setup paths
    base_dir = Path(__file__).parent
    source = Path(source_path)
    vectorstore_path = base_dir / "vectorstores" / vectorstore_name
    
    print("=" * 60)
    print(f"Processing: {source}")
    print(f"Output: {vectorstore_path}")
    print("=" * 60)
    
    # Validate source
    if not source.exists():
        print(f"❌ ERROR: Source path does not exist: {source}")
        return False
    
    # Step 1: Process documents
    print("\n[1/3] Processing documents...")
    processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
    
    try:
        if source.is_file():
            # Single file
            documents = processor.load_pdf(str(source))
            chunks = processor.chunk_documents(documents)
            print(f"✓ Processed 1 file into {len(chunks)} chunks")
        else:
            # Directory
            chunks = processor.process_directory(str(source))
            print(f"✓ Processed directory into {len(chunks)} chunks")
        
        if not chunks:
            print("❌ ERROR: No content extracted from documents")
            return False
            
    except Exception as e:
        print(f"❌ ERROR processing documents: {e}")
        return False
    
    # Step 2: Initialize embeddings
    print("\n[2/3] Initializing embeddings...")
    try:
        embedding_manager = EmbeddingManager()
        print("✓ Embeddings ready (using all-MiniLM-L6-v2)")
    except Exception as e:
        print(f"❌ ERROR initializing embeddings: {e}")
        return False
    
    # Step 3: Create and save FAISS vectorstore
    print("\n[3/3] Creating FAISS vectorstore...")
    try:
        store_manager = VectorStoreManager(
            embedding_manager,
            store_path=str(vectorstore_path)
        )
        
        # Create vectorstore
        store_manager.create_vector_store(chunks)
        
        # Save to disk
        store_manager.save_vector_store()
        
        print(f"✓ Vectorstore saved to: {vectorstore_path}")
        
    except Exception as e:
        print(f"❌ ERROR creating vectorstore: {e}")
        return False
    
    # Test the vectorstore
    print("\n" + "=" * 60)
    print("Testing Vectorstore")
    print("=" * 60)
    
    test_query = "Summarize the main content"
    print(f"\nTest Query: '{test_query}'")
    
    try:
        results = store_manager.similarity_search(test_query, k=2)
        print(f"✓ Found {len(results)} results")
        
        if results:
            doc = results[0]
            print(f"\nTop Result:")
            print(f"  Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"  Page: {doc.metadata.get('page', 'N/A')}")
            print(f"  Preview: {doc.page_content[:200]}...")
    except Exception as e:
        print(f"⚠ Warning: Could not test search: {e}")
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS! Vectorstore created and saved")
    print("=" * 60)
    print(f"\nVectorstore name: '{vectorstore_name}'")
    print(f"Location: {vectorstore_path}")
    print(f"\nYou can now use this vectorstore in your agent with:")
    print(f"  extract_medical_info('{vectorstore_name}')")
    
    return True


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print(__doc__)
        print("\n❌ ERROR: Invalid arguments")
        print("\nUsage: python process_document.py <source_path> <vectorstore_name>")
        sys.exit(1)
    
    source_path = sys.argv[1]
    vectorstore_name = sys.argv[2]
    
    success = process_and_store(source_path, vectorstore_name)
    
    if not success:
        print("\n❌ Failed to process documents")
        sys.exit(1)
    
    print("\n✅ All done!")


if __name__ == "__main__":
    main()
