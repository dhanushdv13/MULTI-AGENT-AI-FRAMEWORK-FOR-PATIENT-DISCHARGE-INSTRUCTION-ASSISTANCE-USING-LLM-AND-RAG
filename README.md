Here is your **rewritten README content** (clean, structured, and ready to paste into GitHub). I kept everything **complete, clear, and professional** while preserving your original meaning.

---

# 🧠 AI Insurance Agent — Complete Project Explanation

## 📑 Table of Contents

1. Project Overview
2. Architecture & System Flow
3. Backend Deep Dive
4. Frontend Deep Dive
5. Database Layer
6. AI Pipeline (Core Intelligence)
7. Running the Project
8. File Structure

---

## 🚀 1. Project Overview

This project is a **Medical Discharge Document Analysis Web Application** called **Dischargo**.

It enables patients or hospital staff to:

* Upload hospital discharge PDFs (reports, bills, summaries)
* Extract text using OCR (Optical Character Recognition)
* Convert extracted text into vector embeddings for AI processing
* Interact with documents through a chat interface

💬 Example queries:

* *“What medicines were prescribed?”*
* *“Generate a diet plan based on my condition”*

### 🧩 Key Feature: Multi-Agent AI System

Different AI agents handle different tasks:

* Discharge analysis
* Diet planning
* Bill validation

---

## 🛠️ Tech Stack

| Layer      | Technology                       |
| ---------- | -------------------------------- |
| Frontend   | Next.js 14, React 18, TypeScript |
| Styling    | Tailwind CSS                     |
| State Mgmt | Zustand, React Query             |
| Backend    | FastAPI (Python)                 |
| Database   | MongoDB (Motor async driver)     |
| AI/LLM     | Google Gemini (via LangChain)    |
| Embeddings | Sentence Transformers            |
| Vector DB  | FAISS                            |
| OCR        | RapidOCR + PyMuPDF               |
| Auth       | JWT + bcrypt                     |

---

## 🏗️ 2. Architecture & Flow

### 🔄 System Flow

1. User opens frontend (Next.js)
2. Logs in → Backend validates → JWT token returned
3. Uploads PDF → Backend processes:

   * Extract text (OCR)
   * Generate embeddings (FAISS)
4. User asks a question → Backend:

   * Retrieves relevant chunks
   * Sends to Gemini
   * Returns response

---

## ⚙️ 3. Backend Deep Dive

### 🔹 Entry Point (`main.py`)

* Initializes FastAPI app
* Enables CORS
* Registers routes (auth, uploads, chat)
* Creates DB indexes on startup

---

### 🔹 Configuration (`config.py`)

Handles environment variables:

* MongoDB URI
* JWT secrets
* Gemini API key
* Model settings (temperature, embeddings)

---

### 🔹 Security (`security.py`)

* Password hashing using bcrypt
* JWT token creation & validation

---

### 🔹 Auth Dependency (`deps.py`)

* Extracts user from token
* Validates authentication
* Protects API routes

---

### 🔹 Database (`mongo.py`)

Collections:

* users
* uploads
* chat_history

---

### 🔹 Indexing (`init_indexes.py`)

* Improves query speed
* Enforces unique users

---

### 🔹 Data Models (Pydantic)

Defines structured data:

* User
* Chat messages
* Upload metadata

---

### 🔹 Auth Routes

* `/auth/register` → Create user
* `/auth/login` → Authenticate & return JWT

---

### 🔹 Upload Pipeline (`uploads.py`)

Handles full document lifecycle:

1. Upload file
2. Save metadata
3. Run background processing:

   * OCR extraction
   * Embedding generation
   * Word document creation
4. Update status

---

### 🔹 Chat System (`chat.py`)

* Verifies document ownership
* Uses orchestrator to route query
* Returns AI response

---

## 🤖 4. AI Pipeline — The Brain

### 🔹 Document Processing

* Extracts text from PDFs
* Uses OCR if needed
* Splits into meaningful chunks

---

### 🔹 Embeddings

* Converts text → vectors
* Uses Sentence Transformers
* Enables semantic search

---

### 🔹 Vector Store (FAISS)

* Stores document embeddings
* Performs similarity search

---

### 🔹 Orchestrator

Acts as a decision engine:

* Classifies query
* Selects correct agent
* Routes request

---

### 🔹 AI Agents

#### 🏥 Discharge Agent

* Answers medical queries
* Extracts summaries & medications

#### 🥗 Diet Agent

* Generates diet plans
* Suggests foods to avoid

---

### 🔹 PDF → Word Conversion

* Converts extracted content
* Maintains formatting
* Avoids reprocessing using cache

---

## 💻 5. Frontend Deep Dive

### 🔹 API Client (`api.ts`)

* Handles all HTTP requests
* Automatically attaches JWT
* Redirects on auth failure

---

### 🔹 Auth Hook

* login()
* register()
* logout()

---

### 🔹 Pages (Next.js Routing)

| Route                | Purpose      |
| -------------------- | ------------ |
| /login               | Login page   |
| /register            | Registration |
| /dashboard/files     | File list    |
| /dashboard/upload    | Upload       |
| /dashboard/files/:id | Chat         |

---

### 🔹 Key Libraries

* Axios
* Zustand
* React Query
* Framer Motion
* React Markdown

---

## ▶️ 6. How to Run the Project

### 🔧 Prerequisites

* Python 3.12+
* Node.js 18+
* MongoDB

---

### 🖥️ Backend Setup

```bash
cd backend
python -m venv backendenv
source backendenv/bin/activate
pip install -r app/requirements.txt

# Create .env file
MONGO_URI=mongodb://localhost:27017
JWT_SECRET=your-secret
GOOGLE_API_KEY=your-api-key

uvicorn app.main:app --reload --port 8000
```

---

### 🌐 Frontend Setup

```bash
cd frontend
npm install

# Create .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
```

---

### 🌍 Open App

```
http://localhost:3000
```

---

## 📁 7. Project Structure

ai-insurance-agent-dev-phase1/
│
├── 📄 SETUP.md
├── 📄 .gitignore
│
├── 🖥️ backend/
│   ├── 📄 .env.example
│   ├── 📄 AI_README.md
│   ├── 📄 requirements.txt
│   │
│   ├── 📦 app/
│   │   ├── 📄 main.py                # FastAPI entry point
│   │
│   │   ├── ⚙️ core/
│   │   │   ├── config.py             # Environment & settings
│   │   │   ├── security.py           # JWT & password hashing
│   │   │   ├── deps.py               # Auth dependency (current user)
│   │   │
│   │   ├── 🗄️ db/
│   │   │   ├── mongo.py              # MongoDB connection
│   │   │   ├── init_indexes.py       # DB indexing
│   │   │
│   │   ├── 🧾 models/
│   │   │   ├── auth.py               # Login model
│   │   │   ├── user.py               # User schema
│   │   │   ├── chat.py               # Chat models
│   │   │   ├── upload.py             # Upload schema
│   │   │
│   │   ├── 🌐 routes/
│   │   │   ├── auth.py               # /auth APIs
│   │   │   ├── uploads.py            # Upload pipeline APIs
│   │   │   ├── chat.py               # Chat APIs
│   │   │
│   │   ├── 🤖 ai/
│   │   │   ├── documents.py          # Metadata schema
│   │   │   ├── processor.py          # OCR + text extraction
│   │   │   ├── pdf_to_word.py        # PDF → DOCX conversion
│   │   │   ├── orchestrator.py       # AI router
│   │   │
│   │   │   ├── 🧠 agents/
│   │   │   │   ├── base.py           # Base agent logic
│   │   │   │   ├── discharge_agent.py # Medical Q&A agent
│   │   │   │   ├── diet_agent.py     # Diet planning agent
│   │   │   │   ├── bill_agent.py     # Bill validation (placeholder)
│   │   │   │   ├── medicine_agent.py # Medicine info (placeholder)
│   │   │
│   │   │   ├── 📊 vectorstore/
│   │   │   │   ├── embeddings.py     # Text → vectors
│   │   │   │   ├── store.py          # FAISS index management
│   │   │
│   │   │   ├── 🌐 scrapers/
│   │   │   │   ├── pharmacy.py       # Medicine price scraper
│   │
│   │
│   ├── 📁 data/                     # (Generated at runtime)
│   │   ├── uploads/                 # Uploaded PDFs
│   │   ├── vectors/                 # FAISS indexes
│   │
│   ├── 🐍 venv/                     # Virtual environment
│
│
├── 🌐 frontend/
│   ├── 📄 package.json
│   ├── 📄 next.config.js
│   ├── 📄 tailwind.config.ts
│   ├── 📄 tsconfig.json
│   │
│   ├── 📁 src/
│   │   ├── 🎨 app/
│   │   │   ├── globals.css
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx              # Redirect → login
│   │   │   ├── not-found.tsx
│   │   │
│   │   │   ├── 🔐 login/
│   │   │   │   ├── page.tsx
│   │   │
│   │   │   ├── 📝 register/
│   │   │   │   ├── page.tsx
│   │   │
│   │   │   ├── 📊 dashboard/
│   │   │   │   ├── layout.tsx        # Sidebar layout
│   │   │   │
│   │   │   │   ├── 📂 upload/
│   │   │   │   │   ├── page.tsx
│   │   │   │
│   │   │   │   ├── 📁 files/
│   │   │   │   │   ├── page.tsx      # File list
│   │   │   │   │
│   │   │   │   │   ├── [id]/
│   │   │   │   │   │   ├── page.tsx          # Chat UI
│   │   │   │   │   │   ├── content/page.tsx  # View PDF
│   │   │   │   │   │   ├── extracted/page.tsx # Extracted text
│   │   │
│   │   ├── 🧩 components/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── ProtectedRoute.tsx
│   │   │
│   │   ├── 🔔 context/
│   │   │   ├── ToastContext.tsx
│   │   │
│   │   ├── 🪝 hooks/
│   │   │   ├── useAuth.ts
│   │   │
│   │   ├── 🔗 lib/
│   │   │   ├── api.ts                # Axios client
│   │   │
│   │   ├── 🧾 types/
│   │   │   ├── index.ts              # TypeScript interfaces
│
│
├── 📁 GIG/                          # Reference implementation
│
└── 📁 README.md                     # Your GitHub README
```

---

## 🎯 Final Summary

This project demonstrates:

* ✅ Full-stack AI application development
* ✅ RAG (Retrieval-Augmented Generation) system
* ✅ Multi-agent AI architecture
* ✅ Scalable backend + modern frontend
* ✅ Real-world healthcare use case
