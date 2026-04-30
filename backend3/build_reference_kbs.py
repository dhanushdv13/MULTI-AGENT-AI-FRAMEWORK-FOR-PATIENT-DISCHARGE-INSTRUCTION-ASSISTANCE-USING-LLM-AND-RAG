"""
build_reference_kbs.py
---------------------------------------------------------
One-shot script to build ALL static reference knowledge bases:

  1. vectorstores/diet_docs    ← from shared/diet_docs/*.pdf
  2. vectorstores/cghs_rates   ← from shared/bill_docs/Cghs_Rate_List1500.00.xlsx
  3. vectorstores/nppa_prices  ← from shared/bill_docs/NPPA-UPDATED-PRICE-LIST-*.pdf

Run once before starting the backend:
    python build_reference_kbs.py
"""

from pathlib import Path

import pandas as pd

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from rag import embed_instance
from rag.pdf_processor import PDFProcessor


# ─────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────

BASE_DIR         = Path(__file__).parent
VECTOR_STORES_DIR = BASE_DIR / "vectorstores"
SHARED_DIR       = BASE_DIR / "shared"

DIET_DOCS_DIR    = SHARED_DIR / "diet_docs"
BILL_DOCS_DIR    = SHARED_DIR / "bill_docs"
CGHS_FILE        = BILL_DOCS_DIR / "Cghs_Rate_List1500.00.xlsx"
NPPA_FILE        = BILL_DOCS_DIR / "NPPA-UPDATED-PRICE-LIST-AS-ON-01-04-2025_compressed-1_compressed.pdf"

# Shared embeddings instance (all-MiniLM-L6-v2)
embeddings = embed_instance.get_embeddings()


# ─────────────────────────────────────────────────────────────
# 1. DIET KB  (vectorstores/diet_docs)
# ─────────────────────────────────────────────────────────────

def build_diet_kb():
    print("=" * 60)
    print("Building Diet KB  →  vectorstores/diet_docs")
    print("=" * 60)

    vector_store_path = VECTOR_STORES_DIR / "diet_docs"

    print(f"  Source : {DIET_DOCS_DIR}")
    print(f"  Output : {vector_store_path}")

    # Step 1: Process PDFs into chunks
    print("\n[1/3] Processing PDF documents...")
    processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
    try:
        chunks = processor.process_directory(str(DIET_DOCS_DIR))
        if not chunks:
            print("ERROR: No documents processed. Make sure PDFs exist in shared/diet_docs/")
            return False
        print(f"  ✓ {len(chunks)} chunks created")
    except Exception as e:
        print(f"  ERROR processing PDFs: {e}")
        return False

    # Step 2: Create and save vector store (uses shared embeddings)
    print("\n[2/3] Creating FAISS vector store...")
    try:
        vectorstore = FAISS.from_documents(chunks, embeddings)
        vectorstore.save_local(str(vector_store_path))
        print("  ✓ Vector store saved")
    except Exception as e:
        print(f"  ERROR creating vector store: {e}")
        return False

    # Step 3: Quick sanity check
    print("\n[3/3] Validating vector store...")
    try:
        vs = FAISS.load_local(str(vector_store_path), embeddings, allow_dangerous_deserialization=True)
        results = vs.similarity_search("What are the dietary recommendations for diabetes?", k=2)
        print(f"  ✓ Validation OK — {len(results)} results returned")
    except Exception as e:
        print(f"  WARNING: Validation failed: {e}")

    print("\n✅ Diet KB built successfully!\n")
    return True


# ─────────────────────────────────────────────────────────────
# 2. CGHS KB  (vectorstores/cghs_rates)
# ─────────────────────────────────────────────────────────────

def build_cghs_kb():
    print("=" * 60)
    print("Building CGHS KB  →  vectorstores/cghs_rates")
    print("=" * 60)

    vector_store_path = VECTOR_STORES_DIR / "cghs_rates"

    print(f"  Source : {CGHS_FILE}")
    print(f"  Output : {vector_store_path}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)

    # Step 1: Load Excel — each row becomes a Document
    print("\n[1/3] Loading CGHS Excel file...")
    try:
        df = pd.read_excel(CGHS_FILE)
        documents = []
        for _, row in df.iterrows():
            row_text = "\n".join([f"{col}: {row[col]}" for col in df.columns])
            documents.append(
                Document(page_content=row_text, metadata={"source": "CGHS_RATE_LIST"})
            )
        print(f"  ✓ {len(documents)} rows loaded")
    except Exception as e:
        print(f"  ERROR loading Excel: {e}")
        return False

    # Step 2: Split & embed
    print("\n[2/3] Splitting and embedding...")
    try:
        split_docs = splitter.split_documents(documents)
        vectorstore = FAISS.from_documents(split_docs, embeddings)
        print(f"  ✓ {len(split_docs)} chunks embedded")
    except Exception as e:
        print(f"  ERROR during embedding: {e}")
        return False

    # Step 3: Save
    print("\n[3/3] Saving vector store...")
    try:
        vectorstore.save_local(str(vector_store_path))
        print("  ✓ Vector store saved")
    except Exception as e:
        print(f"  ERROR saving: {e}")
        return False

    print("\n✅ CGHS KB built successfully!\n")
    return True


# ─────────────────────────────────────────────────────────────
# 3. NPPA KB  (vectorstores/nppa_prices)
# ─────────────────────────────────────────────────────────────

def build_nppa_kb():
    print("=" * 60)
    print("Building NPPA KB  →  vectorstores/nppa_prices")
    print("=" * 60)

    vector_store_path = VECTOR_STORES_DIR / "nppa_prices"

    print(f"  Source : {NPPA_FILE}")
    print(f"  Output : {vector_store_path}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)

    # Step 1: Load PDF
    print("\n[1/3] Loading NPPA PDF...")
    try:
        loader = PyPDFLoader(str(NPPA_FILE))
        docs = loader.load()
        print(f"  ✓ {len(docs)} pages loaded")
    except Exception as e:
        print(f"  ERROR loading PDF: {e}")
        return False

    # Step 2: Split & embed
    print("\n[2/3] Splitting and embedding...")
    try:
        split_docs = splitter.split_documents(docs)
        vectorstore = FAISS.from_documents(split_docs, embeddings)
        print(f"  ✓ {len(split_docs)} chunks embedded")
    except Exception as e:
        print(f"  ERROR during embedding: {e}")
        return False

    # Step 3: Save
    print("\n[3/3] Saving vector store...")
    try:
        vectorstore.save_local(str(vector_store_path))
        print("  ✓ Vector store saved")
    except Exception as e:
        print(f"  ERROR saving: {e}")
        return False

    print("\n✅ NPPA KB built successfully!\n")
    return True


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    VECTOR_STORES_DIR.mkdir(exist_ok=True)

    results = {
        "diet_docs":   build_diet_kb(),
        "cghs_rates":  build_cghs_kb(),
        "nppa_prices": build_nppa_kb(),
    }

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for kb, ok in results.items():
        status = "✅ OK" if ok else "❌ FAILED"
        print(f"  {kb:<20} {status}")

    if all(results.values()):
        print("\n🎉 All reference KBs built successfully!")
    else:
        print("\n⚠️  Some KBs failed. Check errors above.")
        exit(1)

