"""
Setup Knowledge Base - Index shared regulatory and dietary documents
Run this script once to populate the shared vector stores
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.documents.processor import extract_text_from_pdf, smart_chunk_text
from app.vectorstore.store import (
    get_regulations_store,
    get_dietary_store,
    get_insurance_store,
)

print("=" * 70)
print("KNOWLEDGE BASE SETUP - Indexing Shared Documents")
print("=" * 70)


def index_regulations():
    """Index NPPA and CGHS regulatory documents."""
    print("\n[1/3] Indexing Regulations (NPPA, CGHS)...")
    
    regulations_dir = settings.BASE_DIR / "docs" / "regulations"
    store = get_regulations_store()
    
    if not store.is_empty():
        print("  ⚠️  Regulations store already has data. Skipping...")
        return
    
    all_chunks = []
    
    # Index all PDFs in regulations folder
    for pdf_file in regulations_dir.glob("*.pdf"):
        print(f"  📄 Processing: {pdf_file.name}")
        try:
            full_text, pages_data = extract_text_from_pdf(str(pdf_file))
            
            chunk_index = 0
            for page_data in pages_data:
                page_num = page_data["page_num"]
                page_text = page_data.get("text", "")
                
                if not page_text:
                    continue
                
                chunks = smart_chunk_text(
                    page_text,
                    page_num,
                    chunk_size=settings.CHUNK_SIZE,
                    chunk_overlap=settings.CHUNK_OVERLAP,
                )
                
                for chunk_text, chunk_type in chunks:
                    metadata = {
                        "source": "regulations",
                        "filename": pdf_file.name,
                        "doc_type": "regulation",
                        "page_num": page_num,
                        "chunk_type": chunk_type,
                        "chunk_index": chunk_index,
                    }
                    
                    # Determine regulation type
                    if "nppa" in pdf_file.name.lower():
                        metadata["regulation_type"] = "nppa"
                    elif "cghs" in pdf_file.name.lower():
                        metadata["regulation_type"] = "cghs"
                    else:
                        metadata["regulation_type"] = "general"
                    
                    all_chunks.append({
                        "content": chunk_text,
                        "metadata": metadata,
                    })
                    
                    chunk_index += 1
            
            print(f"    ✓ Extracted {len(all_chunks)} chunks")
            
        except Exception as e:
            print(f"    ✗ Error processing {pdf_file.name}: {e}")
    
    # Index text files too
    for txt_file in regulations_dir.glob("*.txt"):
        print(f"  📄 Processing: {txt_file.name}")
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                full_text = f.read()
            
            chunks = smart_chunk_text(
                full_text,
                page_num=1,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
            
            chunk_index = 0
            for chunk_text, chunk_type in chunks:
                metadata = {
                    "source": "regulations",
                    "filename": txt_file.name,
                    "doc_type": "regulation",
                    "page_num": 1,
                    "chunk_type": chunk_type,
                    "chunk_index": chunk_index,
                }
                
                if "nppa" in txt_file.name.lower():
                    metadata["regulation_type"] = "nppa"
                elif "cghs" in txt_file.name.lower():
                    metadata["regulation_type"] = "cghs"
                else:
                    metadata["regulation_type"] = "general"
                
                all_chunks.append({
                    "content": chunk_text,
                    "metadata": metadata,
                })
                
                chunk_index += 1
            
            print(f"    ✓ Extracted {chunk_index} chunks")
            
        except Exception as e:
            print(f"    ✗ Error processing {txt_file.name}: {e}")
    
    # Add to vector store
    if all_chunks:
        print(f"  💾 Indexing {len(all_chunks)} chunks into FAISS...")
        store.add_documents(all_chunks)
        print(f"  ✓ Regulations indexed successfully!")
    else:
        print("  ⚠️  No chunks extracted from regulations")


def index_dietary_guidelines():
    """Index dietary guidelines PDFs."""
    print("\n[2/3] Indexing Dietary Guidelines...")
    
    dietary_dir = settings.BASE_DIR / "docs" / "dietary_guide"
    store = get_dietary_store()
    
    if not store.is_empty():
        print("  ⚠️  Dietary store already has data. Skipping...")
        return
    
    all_chunks = []
    
    for pdf_file in dietary_dir.glob("*.pdf"):
        print(f"  📄 Processing: {pdf_file.name}")
        try:
            full_text, pages_data = extract_text_from_pdf(str(pdf_file))
            
            chunk_index = 0
            for page_data in pages_data:
                page_num = page_data["page_num"]
                page_text = page_data.get("text", "")
                
                if not page_text:
                    continue
                
                chunks = smart_chunk_text(
                    page_text,
                    page_num,
                    chunk_size=settings.CHUNK_SIZE,
                    chunk_overlap=settings.CHUNK_OVERLAP,
                )
                
                for chunk_text, chunk_type in chunks:
                    metadata = {
                        "source": "dietary_guide",
                        "filename": pdf_file.name,
                        "doc_type": "dietary",
                        "page_num": page_num,
                        "chunk_type": chunk_type,
                        "chunk_index": chunk_index,
                    }
                    
                    all_chunks.append({
                        "content": chunk_text,
                        "metadata": metadata,
                    })
                    
                    chunk_index += 1
            
            print(f"    ✓ Extracted {len(all_chunks)} chunks")
            
        except Exception as e:
            print(f"    ✗ Error processing {pdf_file.name}: {e}")
    
    # Add to vector store
    if all_chunks:
        print(f"  💾 Indexing {len(all_chunks)} chunks into FAISS...")
        store.add_documents(all_chunks)
        print(f"  ✓ Dietary guidelines indexed successfully!")
    else:
        print("  ⚠️  No chunks extracted from dietary guidelines")


def index_insurance_policies():
    """Index insurance policy documents."""
    print("\n[3/3] Indexing Insurance Policies...")
    
    insurance_dir = settings.BASE_DIR / "docs" / "insurance_policies"
    store = get_insurance_store()
    
    if not store.is_empty():
        print("  ⚠️  Insurance store already has data. Skipping...")
        return
    
    all_chunks = []
    
    for pdf_file in insurance_dir.glob("*.pdf"):
        print(f"  📄 Processing: {pdf_file.name}")
        try:
            full_text, pages_data = extract_text_from_pdf(str(pdf_file))
            
            chunk_index = 0
            for page_data in pages_data:
                page_num = page_data["page_num"]
                page_text = page_data.get("text", "")
                
                if not page_text:
                    continue
                
                chunks = smart_chunk_text(
                    page_text,
                    page_num,
                    chunk_size=settings.CHUNK_SIZE,
                    chunk_overlap=settings.CHUNK_OVERLAP,
                )
                
                for chunk_text, chunk_type in chunks:
                    metadata = {
                        "source": "insurance",
                        "filename": pdf_file.name,
                        "doc_type": "insurance",
                        "page_num": page_num,
                        "chunk_type": chunk_type,
                        "chunk_index": chunk_index,
                    }
                    
                    all_chunks.append({
                        "content": chunk_text,
                        "metadata": metadata,
                    })
                    
                    chunk_index += 1
            
            print(f"    ✓ Extracted {len(all_chunks)} chunks")
            
        except Exception as e:
            print(f"    ✗ Error processing {pdf_file.name}: {e}")
    
    # Add to vector store
    if all_chunks:
        print(f"  💾 Indexing {len(all_chunks)} chunks into FAISS...")
        store.add_documents(all_chunks)
        print(f"  ✓ Insurance policies indexed successfully!")
    else:
        print("  ⚠️  No chunks extracted from insurance policies")


def main():
    """Run the complete setup."""
    try:
        # Ensure directories exist
        settings.SHARED_DIR.mkdir(parents=True, exist_ok=True)
        
        # Index all shared documents
        index_regulations()
        index_dietary_guidelines()
        index_insurance_policies()
        
        print("\n" + "=" * 70)
        print("✅ Knowledge Base Setup Complete!")
        print("=" * 70)
        print("\nShared vector stores are now ready for use by agents.")
        
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
