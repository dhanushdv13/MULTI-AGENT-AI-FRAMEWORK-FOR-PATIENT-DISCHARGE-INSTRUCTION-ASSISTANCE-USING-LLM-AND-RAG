# AI Insurance Agent — Complete Project Explanation

## Table of Contents
1. Project Overview
2. Architecture & How Everything Connects
3. Backend Deep Dive (Every File Explained)
4. Frontend Deep Dive (Every File Explained)
5. Database Layer
6. AI Pipeline — The Brain
7. How to Run the Project
8. Complete File Tree

---

## 1. Project Overview

This is a **Medical Discharge Document Analysis** web application called **"Dischargo"**. It allows patients or hospital staff to:

1. **Upload** hospital discharge PDFs (bills, summaries, reports)
2. The AI **reads the PDF** using OCR (Optical Character Recognition)
3. The text is **converted into vector embeddings** (numbers the AI can search)
4. Users can **chat with the AI** about their documents — asking questions like "What medicines were prescribed?" or "Create a diet plan based on my condition"

The system uses a **Multi-Agent Architecture**: different specialized AI "agents" handle different types of questions (discharge analysis, diet planning, bill validation, etc.).

### Tech Stack
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 14 + React 18 + TypeScript | User interface |
| Styling | Tailwind CSS | CSS utility framework |
| State Mgmt | Zustand + React Query | Client-side state |
| HTTP Client | Axios | API calls to backend |
| Backend | FastAPI (Python) | REST API server |
| Database | MongoDB + Motor (async driver) | Data storage |
| AI/LLM | Google Gemini (via LangChain) | Chat responses |
| Embeddings | Sentence-Transformers (all-MiniLM-L6-v2) | Text → vectors |
| Vector DB | FAISS (Facebook AI Similarity Search) | Similarity search |
| OCR | RapidOCR + PyMuPDF | Reading scanned PDFs |
| Auth | JWT + bcrypt | Security |

---

## 2. Architecture — How Everything Connects

```
┌─────────────────────┐         ┌──────────────────────┐
│   FRONTEND (Next.js)│  HTTP   │   BACKEND (FastAPI)   │
│   localhost:3000     │◄──────►│   localhost:8000       │
│                      │        │                        │
│  Login Page ─────────┼──POST──┼─► /auth/login          │
│  Register Page ──────┼──POST──┼─► /auth/register       │
│  Upload Page ────────┼──POST──┼─► /uploads/             │
│  Chat Interface ─────┼──POST──┼─► /chat/{vector_id}    │
│  File List ──────────┼──GET───┼─► /uploads/             │
└─────────────────────┘        └──────────┬───────────────┘
                                          │
                          ┌───────────────┼───────────────┐
                          ▼               ▼               ▼
                    ┌──────────┐   ┌───────────┐   ┌──────────┐
                    │ MongoDB  │   │ FAISS     │   │ Gemini   │
                    │ Database │   │ Vectors   │   │ LLM API  │
                    └──────────┘   └───────────┘   └──────────┘
```

**The flow in plain English:**
1. User opens the website (Frontend) → sees Login page
2. User logs in → Frontend sends credentials to Backend → Backend checks MongoDB → returns a JWT token
3. User uploads a PDF → Backend saves the file, then in the **background**: extracts text (OCR), creates vector embeddings (FAISS), and converts to Word document
4. User asks a question in chat → Backend searches the vectors for relevant text chunks → sends those chunks + the question to Google Gemini → returns the AI's answer

---

## 3. Backend Deep Dive — Every File Explained

### 3.1 Entry Point: `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, uploads, chat
from app.db.mongo import db
from app.db.init_indexes import create_indexes

app = FastAPI(
    title="Medical Backend API",
    version="1.0",
    description="Auth, Uploads, ML-ready APIs"
)

from app.core import config
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await create_indexes(db)

app.include_router(auth.router)
app.include_router(uploads.router)
app.include_router(chat.router)
```

**Line-by-line explanation:**
- `FastAPI(...)` — Creates the web server application. FastAPI auto-generates API documentation at `/docs`.
- `CORSMiddleware` — Without this, your browser would block the frontend (port 3000) from talking to the backend (port 8000). CORS says "these origins are allowed."
- `@app.on_event("startup")` — When the server starts, create database indexes (for faster queries).
- `app.include_router(...)` — Registers three groups of API endpoints: authentication, file uploads, and chat.

---

### 3.2 Configuration: `backend/app/core/config.py`

```python
import os
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "")
JWT_SECRET = os.getenv("JWT_SECRET", "secret")
JWT_ALGO = "HS256"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LLM_MODEL = "gemini-2.5-flash"
LLM_TEMPERATURE = 0.3

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

OCR_DPI = 300
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
```

**What each setting means:**
- `load_dotenv()` — Reads the `.env` file so secrets aren't hardcoded in code
- `MONGO_URI` — Connection string to MongoDB
- `JWT_SECRET` — A secret key used to sign authentication tokens (like a password for your passwords)
- `JWT_ALGO = "HS256"` — The algorithm used to encrypt JWT tokens
- `GOOGLE_API_KEY` — Your API key for Google's Gemini AI
- `LLM_TEMPERATURE = 0.3` — Controls creativity (0 = very precise, 1 = very creative)
- `EMBEDDING_MODEL` — The model that converts text into numbers (384-dimensional vectors)
- `CHUNK_SIZE / CHUNK_OVERLAP` — How documents are split into smaller pieces for processing

---

### 3.3 Security: `backend/app/core/security.py`

```python
from passlib.context import CryptContext
from jose import jwt, JWTError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password.encode("utf-8"))

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password.encode("utf-8"), hashed)

def create_token(data: dict, minutes=60):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=minutes)
    return jwt.encode(payload, config.JWT_SECRET, config.JWT_ALGO)

def decode_token(token: str):
    try:
        return jwt.decode(token, config.JWT_SECRET, [config.JWT_ALGO])
    except JWTError:
        return None
```

**What this does:**
- `hash_password` — Takes "mypassword123" and turns it into a scrambled string like "$2b$12$abc...". This is stored in the database. Even if someone steals the database, they can't read passwords.
- `verify_password` — Checks if a plain password matches the scrambled version.
- `create_token` — Creates a JWT token (a signed string containing the user_id and expiration time). This token is sent to the frontend and included in every subsequent request.
- `decode_token` — Reads and verifies a JWT token. If it's expired or tampered with, returns None.

---

### 3.4 Auth Protection: `backend/app/core/deps.py`

```python
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def current_user(token: str = Depends(oauth2)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")
    user = await users.find_one({"_id": ObjectId(payload["user_id"])})
    if not user:
        raise HTTPException(401, "User not found")
    return user
```

**What this does:** This is a "dependency" — a reusable function that runs before any protected API endpoint. When an endpoint has `user=Depends(current_user)`, FastAPI automatically: extracts the token from the `Authorization: Bearer <token>` header → decodes it → looks up the user in MongoDB → passes the user object to the endpoint. If anything fails, it returns a 401 Unauthorized error.

---

### 3.5 Database: `backend/app/db/mongo.py`

```python
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(config.MONGO_URI)
db = client.medical_db

users = db.users
uploads = db.uploads
chat_history = db.chat_history
```

**What this does:** Motor is the async MongoDB driver for Python. This creates a connection to MongoDB and defines three **collections** (like tables): `users`, `uploads`, and `chat_history`. These are imported by other files to read/write data.

### 3.6 Database Indexes: `backend/app/db/init_indexes.py`

```python
async def create_indexes(db):
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True)
    await db.uploads.create_index("user_id")
    await db.uploads.create_index("vector_status")
```

**What this does:** Indexes make database queries faster (like an index in a book). `unique=True` ensures no two users can have the same username or email.

---

### 3.7 Data Models: `backend/app/models/`

These are **Pydantic models** — they define the shape of data and automatically validate it.

**user.py — What user data looks like:**
```python
class RegisterUser(BaseModel):
    full_name: str
    username: str
    email: EmailStr      # Validates email format automatically
    mobile: str
    age: int
    gender: str
    address: Optional[str] = None  # Optional field
    password: str
```

**chat.py — What chat messages look like:**
```python
class ChatMessage(BaseModel):     # What the user sends
    message: str

class ChatResponse(BaseModel):    # What the server returns
    agent: str                     # Which AI agent answered
    response: str                  # The answer text
    vector_id: str                 # Which document was queried
```

**upload.py — What upload records look like:**
```python
class UploadOut(BaseModel):
    upload_id: str
    user_id: str
    filename: str
    vector_status: str       # "PROCESSING", "COMPLETED", or "FAILED"
    vector_id: Optional[str] # Links to the FAISS vector index
```

---

### 3.8 Routes: `backend/app/routes/auth.py`

```python
router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
async def register(data: RegisterUser):
    doc = {
        "full_name": data.full_name,
        "username": data.username,
        "password": hash_password(data.password),  # NEVER store plain passwords
        "created_at": datetime.utcnow(),
    }
    res = await users.insert_one(doc)
    return {"user_id": str(res.inserted_id)}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await users.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"user_id": str(user["_id"])})
    return {"access_token": token, "token_type": "bearer"}
```

**Register flow:** Receives user data → hashes the password → saves to MongoDB → returns the new user ID.
**Login flow:** Receives username+password → finds user in DB → verifies password → creates a JWT token → returns it. The frontend stores this token and sends it with every future request.

---

### 3.9 Routes: `backend/app/routes/uploads.py` (Most Complex File)

This file handles the entire file upload pipeline. Key sections:

**Upload endpoint (`POST /uploads/`):**
1. Generates unique IDs for the upload and its vector index
2. Saves the uploaded file to `data/uploads/`
3. Creates a database record with status "PROCESSING"
4. Triggers a **background task** (so the user doesn't wait)
5. Returns immediately with the upload ID

**Background processing function (`process_upload_background`):**
1. **Step 1:** Calls `process_document()` to extract text using OCR and create chunks
2. **Step 2:** Calls `add_document_to_index_async()` to generate embeddings and store in FAISS
3. **Step 3:** Calls `pdf_to_word()` to create a downloadable Word document
4. Updates the database status to "COMPLETED" or "FAILED"

**Other endpoints:**
- `GET /uploads/` — List all uploads for the logged-in user
- `GET /uploads/{id}` — Get details of a single upload
- `GET /uploads/{id}/content` — Download the original PDF
- `GET /uploads/{id}/extracted` — Download the Word document
- `GET /uploads/{id}/extracted/html` — View extracted content as HTML (uses `mammoth` library)

---

### 3.10 Routes: `backend/app/routes/chat.py`

```python
@router.post("/{vector_id}", response_model=ChatResponse)
async def chat_with_file(vector_id: str, chat_msg: ChatMessage, user=Depends(current_user)):
    # 1. Verify this document belongs to the user
    upload = await uploads.find_one({"vector_id": vector_id, "user_id": str(user["_id"])})
    if not upload:
        raise HTTPException(status_code=404, detail="File context not found")

    # 2. Create an Orchestrator and process the query
    orchestrator = Orchestrator(vector_id=vector_id)
    result = await orchestrator.process_query(chat_msg.message)

    return ChatResponse(agent=result["agent"], response=result["response"], vector_id=vector_id)
```

**What this does:** When a user sends a chat message, this endpoint: verifies the user owns the document → creates an Orchestrator (the AI manager) → the orchestrator classifies the query and routes it to the right agent → returns the agent's response.

---

## 4. The AI Pipeline — The Brain

### 4.1 Document Processor: `backend/app/ai/processor.py`

This is where PDFs are read and turned into searchable text. The key function is `process_document()`:

1. **Text Extraction** (`extract_text_from_pdf`): Opens the PDF with PyMuPDF. For each page:
   - First tries **native text extraction** (for digital PDFs)
   - If a page has very little text (<50 characters), it's probably a **scanned image**, so it runs **OCR** using RapidOCR
2. **OCR Caching**: Saves the extracted text to a JSON file so it doesn't need to re-OCR later
3. **Smart Chunking** (`smart_chunking`): Splits the full text into smaller pieces (~1000 characters each, with 200-character overlap). It splits at paragraph boundaries so chunks make semantic sense.
4. **Metadata**: Each chunk gets tagged with user_id, upload_id, vector_id, filename, page number, etc.

### 4.2 Embeddings: `backend/app/ai/vectorstore/embeddings.py`

```python
_embedding_model = None  # Lazy singleton

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
    return _embedding_model

def embed_texts(texts):
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()
```

**What this does:** The embedding model converts text into 384-dimensional number arrays. For example, "heart surgery" might become `[0.23, -0.45, 0.12, ...]`. Similar texts produce similar number arrays. The model is **lazy loaded** — it only loads into memory the first time it's needed (~30 seconds), keeping server startup fast.

### 4.3 Vector Store: `backend/app/ai/vectorstore/store.py`

This manages FAISS indexes — one per uploaded document.

**Adding documents:**
1. Takes text chunks → generates embeddings → adds to a FAISS index
2. Saves the index and metadata to disk at `data/vectors/{vector_id}/faiss_index/`

**Searching:**
1. Converts the user's question into an embedding
2. FAISS finds the most similar chunks using L2 distance (Euclidean distance)
3. Returns the top-k most relevant chunks with their metadata

There are also **SharedVectorStores** for regulations, dietary guidelines, and insurance policies that are shared across all users.

### 4.4 The Orchestrator: `backend/app/ai/orchestrator.py`

The orchestrator is the **traffic controller**. When a query comes in:

1. **Classification**: Sends the query to Gemini with a prompt like "Which agent should handle this?" The LLM picks between Diet Agent and Discharge Agent.
2. **Fallback**: If the LLM's response doesn't match any agent name, it uses keyword matching (e.g., if "diet" or "food" is in the query → Diet Agent).
3. **Delegation**: Passes the query to the selected agent's `process_async()` method.

### 4.5 The Agents: `backend/app/ai/agents/`

**BaseAgent** (`base.py`): Provides common functionality:
- `search_current_document_async()` — Searches the document's FAISS index
- `ask_llm_async()` — Sends a prompt to Google Gemini
- Helper methods for searching discharge, bills, dietary guidelines, etc.

**DischargeSummaryAgent** (`discharge_agent.py`): Handles medical questions. It:
1. Searches the document for relevant chunks (RAG — Retrieval Augmented Generation)
2. Builds a prompt with a system instruction + the relevant chunks + the user's question
3. Sends everything to Gemini and returns the response
4. Has special methods: `get_summary()` (full document summary) and `extract_medications()` (medication table)

**DietPlanningAgent** (`diet_agent.py`): Handles nutrition questions. It:
1. Searches the discharge document for medical conditions
2. Also searches shared dietary guidelines
3. Combines both contexts and sends to Gemini
4. Has special methods: `generate_meal_plan()` and `foods_to_avoid()`

### 4.6 PDF to Word: `backend/app/ai/pdf_to_word.py`

Converts the uploaded PDF into a formatted Word document (.docx). It:
1. Uses the OCR cache (from processor.py) to avoid re-running OCR
2. Detects headings, key-value pairs, and table-like structures
3. Builds a Word document with proper formatting (bold headings, tables with grid, compact layout)

---

## 5. Frontend Deep Dive

### 5.1 API Client: `frontend/src/lib/api.ts`

```typescript
const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});

// Automatically attach JWT token to every request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// If server returns 401, redirect to login
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);
```

**What this does:** Creates a pre-configured Axios HTTP client. **Interceptors** are middleware that run on every request/response. The request interceptor automatically adds the auth token. The response interceptor handles expired tokens by redirecting to login.

### 5.2 Auth Hook: `frontend/src/hooks/useAuth.ts`

A custom React hook that provides `login()`, `register()`, `logout()`, and `isAuthenticated()` functions. On login, it stores the JWT token in `localStorage`. On logout, it removes it.

### 5.3 Type Definitions: `frontend/src/types/index.ts`

TypeScript interfaces that define data shapes (User, Upload, ChatMessage, ChatResponse, etc.) ensuring type safety across the frontend.

### 5.4 Pages (Next.js File-Based Routing)

| File Path | URL | Purpose |
|-----------|-----|---------|
| `src/app/page.tsx` | `/` | Redirects to `/login` |
| `src/app/login/page.tsx` | `/login` | Login form |
| `src/app/register/page.tsx` | `/register` | Registration form |
| `src/app/dashboard/layout.tsx` | `/dashboard/*` | Dashboard shell (sidebar) |
| `src/app/dashboard/files/page.tsx` | `/dashboard/files` | List of uploaded files |
| `src/app/dashboard/upload/page.tsx` | `/dashboard/upload` | Upload new PDF |
| `src/app/dashboard/files/[id]/page.tsx` | `/dashboard/files/:id` | Chat with a specific document |

### 5.5 Key Frontend Dependencies

| Package | Purpose |
|---------|---------|
| `axios` | HTTP requests to backend |
| `zustand` | Lightweight state management |
| `@tanstack/react-query` | Server state caching & synchronization |
| `framer-motion` | Smooth animations |
| `react-markdown` + `remark-gfm` | Renders AI responses as formatted Markdown |

---

## 6. How to Run the Project

### Prerequisites
- Python 3.12+, Node.js 18+, MongoDB running locally

### Step 1: Backend
```bash
cd backend
python -m venv backendenv
source backendenv/bin/activate    # Mac/Linux
pip install -r app/requirements.txt

# Create backend/.env with:
# MONGO_URI=mongodb://localhost:27017
# JWT_SECRET=any-random-string
# GOOGLE_API_KEY=your-gemini-api-key

uvicorn app.main:app --reload --port 8000
```

### Step 2: Frontend
```bash
cd frontend
npm install

# Create frontend/.env.local with:
# NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
```

### Step 3: Open http://localhost:3000

---

## 7. Complete File Tree

```
ai-insurance-agent-dev-phase1/
├── SETUP.md                          # Setup instructions
├── .gitignore
│
├── backend/
│   ├── .env.example                  # Template for environment variables
│   ├── AI_README.md                  # AI integration guide
│   └── app/
│       ├── main.py                   # FastAPI entry point
│       ├── requirements.txt          # Python dependencies
│       ├── core/
│       │   ├── config.py             # All configuration settings
│       │   ├── security.py           # Password hashing & JWT tokens
│       │   └── deps.py               # Auth dependency (current_user)
│       ├── db/
│       │   ├── mongo.py              # MongoDB connection & collections
│       │   └── init_indexes.py       # Database index creation
│       ├── models/
│       │   ├── auth.py               # Login data model
│       │   ├── user.py               # User data models
│       │   ├── chat.py               # Chat message/response models
│       │   └── upload.py             # Upload data models
│       ├── routes/
│       │   ├── auth.py               # /auth/register & /auth/login
│       │   ├── uploads.py            # /uploads/ (CRUD + background processing)
│       │   └── chat.py               # /chat/{vector_id}
│       └── ai/
│           ├── documents.py          # ChunkMetadata schema
│           ├── processor.py          # PDF text extraction & chunking
│           ├── pdf_to_word.py        # PDF → Word conversion
│           ├── orchestrator.py       # Query router (picks the right agent)
│           ├── agents/
│           │   ├── base.py           # BaseAgent with RAG search + LLM
│           │   ├── discharge_agent.py# Medical Q&A agent
│           │   ├── diet_agent.py     # Nutrition planning agent
│           │   ├── bill_agent.py     # (Placeholder) Bill validation
│           │   └── medicine_agent.py # (Placeholder) Medicine prices
│           ├── vectorstore/
│           │   ├── embeddings.py     # Text → 384-dim vectors
│           │   └── store.py          # FAISS index management
│           └── scrapers/
│               └── pharmacy.py       # Web scraper for medicine prices
│
├── frontend/
│   ├── package.json                  # Node.js dependencies
│   ├── next.config.js                # Next.js configuration
│   ├── tailwind.config.ts            # Tailwind CSS configuration
│   ├── tsconfig.json                 # TypeScript configuration
│   └── src/
│       ├── app/
│       │   ├── globals.css           # Global styles
│       │   ├── layout.tsx            # Root HTML layout
│       │   ├── page.tsx              # Home (redirects to /login)
│       │   ├── not-found.tsx         # 404 page
│       │   ├── login/page.tsx        # Login page
│       │   ├── register/page.tsx     # Registration page
│       │   └── dashboard/
│       │       ├── layout.tsx        # Dashboard layout (sidebar)
│       │       ├── upload/page.tsx   # Upload page
│       │       └── files/
│       │           ├── page.tsx      # File listing
│       │           └── [id]/
│       │               ├── page.tsx      # Chat with document
│       │               ├── content/page.tsx   # View original PDF
│       │               └── extracted/page.tsx # View extracted text
│       ├── components/
│       │   ├── Sidebar.tsx           # Navigation sidebar
│       │   └── ProtectedRoute.tsx    # Auth guard component
│       ├── context/
│       │   └── ToastContext.tsx       # Toast notification system
│       ├── hooks/
│       │   └── useAuth.ts            # Authentication hook
│       ├── lib/
│       │   └── api.ts                # Axios HTTP client
│       └── types/
│           └── index.ts              # TypeScript interfaces
│
├── GIG/                              # Reference implementation
└── venv/                             # Python virtual environment
```
