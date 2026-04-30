# 🤖 AI Team Integration Guide

This guide explains how to replace the current mock AI implementation with real models (RAG, Analyzers, etc.) in the Discharge Agent backend.

---

## 🏗️ Architecture Overview

The current backend is built with **FastAPI** and **MongoDB**. The AI logic is currently **mocked** at three key stages:

1.  **Ingestion (OCR)**: When a file is uploaded, we mock the text extraction.
2.  **Vectorization**: We generate a fake `vector_id` instead of storing embeddings.
3.  **Chat (Agent Response)**: We use keyword matching to simulate agent responses.

Your goal is to replace these mocks with real AI services.

---

## � Integration Points

### 1. Ingestion Pipeline (OCR & Vector Embeddings)

**File:** `backend/app/routes/uploads.py`

#### A. OCR Processing
Currently, `mock_extracted_content` is generated in the `upload_file` function.
*   **Action**: Replace the mock string generation with a call to your OCR service (e.g., Tesseract, Azure AI, AWS Textract).
*   **Input**: `file_location` (path to the uploaded PDF/Image).
*   **Output**: Save the extracted text to `extracted_file_path`.

#### B. Vector Embeddings
Currently, `vector_id` is a random string: `f"vec_{upload_id[:8]}"`.
*   **Action**: Generate embeddings for the extracted text and store them in your Vector DB (Pinecone, Weaviate, etc.).
*   **Output**: Get the returned `vector_id` from the DB and save it to MongoDB.

**Code Snippet to Modify (`uploads.py`):**
```python
# CURRENT MOCK
vector_id = f"vec_{upload_id[:8]}" 
mock_extracted_content = f"[MOCKED OCR CONTENT...]"

# REPLACE WITH
text = ocr_service.process(file_location)
vector_id = vector_db.upsert(text, metadata={"filename": file.filename})
```

### 2. Chat Logic (The Brain)

**File:** `backend/app/routes/chat.py`

Currently, `get_mock_agent_response` uses `if "bill" in message: ...` logic.
*   **Action**: Replace this function with a real orchestrator/router.
*   **Input**: User `message` and `upload_data` (context).
*   **Output**: `(agent_name, response_text)`.

---

## 💾 Data Models

**File:** `backend/app/models/upload.py`

The `UploadOut` schema defines what frontend receives and what we store in MongoDB. Key fields for AI:

*   `extracted_content`: (Optional[str]) - Path to the text file containing OCR results.
*   `vector_id`: (Optional[str]) - ID reference to the external Vector DB.
*   `vector_status`: (str) - Status of processing (e.g., "pending", "completed", "failed").

**File:** `backend/app/models/chat.py`

*   `ChatMessage`: Input `{ "message": "Analyze this bill" }`
*   `ChatResponse`: Output `{ "agent": "Bill Validator", "response": "...", "vector_id": "..." }`

---

## 🔑 Configuration

**File:** `backend/app/core/config.py`

You will need to add your API keys here.

1.  **Update `.env`**:
    ```env
    OPENAI_API_KEY=sk-...
    PINECONE_API_KEY=...
    PINECONE_ENV=...
    ```

2.  **Update `config.py`**:
    ```python
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    ```

---

## 📂 Recommended Folder Structure

We recommend creating a dedicated `ai` module to keep logic clean:

```
backend/app/ai/
├── __init__.py
├── orchestrator.py     # Router logic (replaces get_mock_agent_response)
├── services/
│   ├── ocr.py          # Real OCR implementation
│   └── vector_db.py    # Pinecone/Weaviate wrapper
├── agents/             # Specific agent logic
│   ├── bill_validator.py
│   ├── diet_planner.py
│   └── medicine_price.py
└── utils/
    └── rag.py          # RAG implementation
```

## 🛠️ Dependencies

Add your required libraries to `backend/requirements.txt`:
*   `langchain`
*   `openai`
*   `pinecone-client`
*   `tiktoken`
*   `pypdf`

---

**Happy Coding! 🚀**
