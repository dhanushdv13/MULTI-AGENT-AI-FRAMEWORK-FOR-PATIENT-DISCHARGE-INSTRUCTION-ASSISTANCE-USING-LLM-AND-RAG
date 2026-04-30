"""
PDF Processing module for extracting text from PDF documents.
"""
import os
from typing import List
from pathlib import Path
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class PDFProcessor:
    """Handles PDF text extraction and chunking."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize PDF processor.
        
        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_pdf(self, pdf_path: str) -> List[Document]:
        """
        Load a single PDF and extract text.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of Document objects with page content and metadata
        """
        try:
            loader = PyMuPDFLoader(pdf_path)
            documents = loader.load()
            return documents
        except Exception as e:
            print(f"Error loading {pdf_path}: {e}")
            return []
    
    def load_pdfs_from_directory(self, directory_path: str) -> List[Document]:
        """
        Load all PDFs from a directory.
        
        Args:
            directory_path: Path to directory containing PDFs
            
        Returns:
            List of all Document objects from all PDFs
        """
        all_documents = []
        pdf_dir = Path(directory_path)
        
        if not pdf_dir.exists():
            raise ValueError(f"Directory {directory_path} does not exist")
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"Warning: No PDF files found in {directory_path}")
            return []
        
        print(f"Found {len(pdf_files)} PDF files")
        
        for pdf_file in pdf_files:
            print(f"Processing: {pdf_file.name}")
            documents = self.load_pdf(str(pdf_file))
            
            # Add source filename to metadata
            for doc in documents:
                doc.metadata['source'] = pdf_file.name
            
            all_documents.extend(documents)
        
        print(f"Loaded {len(all_documents)} pages from {len(pdf_files)} PDFs")
        return all_documents
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks.
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of chunked Document objects
        """
        chunks = self.text_splitter.split_documents(documents)
        print(f"Created {len(chunks)} chunks from {len(documents)} documents")
        return chunks
    
    def process_directory(self, directory_path: str) -> List[Document]:
        """
        Complete pipeline: load PDFs and chunk them.
        
        Args:
            directory_path: Path to directory containing PDFs
            
        Returns:
            List of chunked Document objects ready for embedding
        """
        documents = self.load_pdfs_from_directory(directory_path)
        if not documents:
            return []
        
        chunks = self.chunk_documents(documents)
        return chunks


if __name__ == "__main__":
    # Test the processor
    processor = PDFProcessor()
    docs_dir = "/home/abhijith/Desktop/Git/ai-insurance-agent/backend2/docs/shared/diet_docs"
    
    chunks = processor.process_directory(docs_dir)
    
    print(f"\nTotal chunks created: {len(chunks)}")
    if chunks:
        print(f"\nSample chunk:")
        print(f"Content: {chunks[0].page_content[:200]}...")
        print(f"Metadata: {chunks[0].metadata}")
