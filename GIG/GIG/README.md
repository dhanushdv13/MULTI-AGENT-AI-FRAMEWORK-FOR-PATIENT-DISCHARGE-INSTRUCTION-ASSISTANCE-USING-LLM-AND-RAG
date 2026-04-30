# Intelligent Multi-Agent Healthcare Assistant for Post-Discharge Support

A comprehensive AI-powered healthcare assistant that helps patients understand discharge summaries, validate hospital bills, compare medicine prices, and get personalized diet plans.

## 🏗️ System Architecture

### Multi-Agent Supervisor Pattern
The system uses the **LangChain supervisor pattern** where specialized agents are wrapped as tools:

```
User Query → Orchestrator (Supervisor) → Specialized Agents → Aggregated Response
                                        ├─ Discharge Summary Agent
                                        ├─ Bill Validator Agent
                                        ├─ Medicine Price Agent
                                        └─ Diet Planning Agent
```

### Key Features

#### 1. **Discharge Summary Agent** (RAG-based)
- Simplifies complex medical terminology
- Explains diagnoses, treatments, and medications
- Extracts and lists all prescribed medicines
- Provides follow-up instructions
- **Citations**: Always includes source (filename, page number)

#### 2. **Bill Validator Agent** (RAG-based)
- Validates hospital bills against NPPA ceiling prices
- Compares against CGHS rates (2025)
- Checks insurance policy limits (room rent, co-payment)
- Identifies overcharging with evidence
- Calculates potential savings

#### 3. **Medicine Price Comparison Agent** (API-based)
- Scrapes real-time prices from:
  - Tata 1mg
  - Apollo Pharmacy
  - PharmEasy
- Identifies cheapest option
- Provides purchase links

#### 4. **Diet Planning Agent** (RAG-based)
- Creates personalized meal plans based on medical conditions
- Considers medication-food interactions
- Indian cuisine focused
- Lists foods to avoid/include
- Provides weekly meal schedules

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10+
- Google Gemini API key (get it from [Google AI Studio](https://ai.google.dev/))

### Installation

1. **Clone and navigate to the project:**
```bash
cd GIG
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
Edit `.env` file and add your Gemini API key:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

4. **Index shared knowledge base (regulations, dietary guidelines):**
```bash
python scripts/setup_knowledge_base.py
```

This will:
- Index NPPA drug price list (2025)
- Index CGHS rate list (2025)
- Index dietary guidelines
- Index insurance policies
- Create FAISS vector stores

Expected output:
```
======================================================================
KNOWLEDGE BASE SETUP - Indexing Shared Documents
======================================================================

[1/3] Indexing Regulations (NPPA, CGHS)...
  📄 Processing: NPPA-UPDATED-PRICE-LIST-AS-ON-01-04-2025.pdf
    ✓ Extracted 2500+ chunks
  📄 Processing: CGHS_rates_2025.txt
    ✓ Extracted 50+ chunks
  💾 Indexing 2550+ chunks into FAISS...
  ✓ Regulations indexed successfully!

[2/3] Indexing Dietary Guidelines...
  📄 Processing: dietary_guidelines.pdf
    ✓ Extracted 300+ chunks
  💾 Indexing 300+ chunks into FAISS...
  ✓ Dietary guidelines indexed successfully!

[3/3] Indexing Insurance Policies...
  📄 Processing: Policy_Star_Comprehensive_Insurance.pdf
    ✓ Extracted 400+ chunks
  💾 Indexing 400+ chunks into FAISS...
  ✓ Insurance policies indexed successfully!

✅ Knowledge Base Setup Complete!
```

5. **Run the FastAPI server:**
```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📡 API Endpoints

### Authentication
- `POST /auth/signup` - Create new user account
- `POST /auth/login` - Login and get JWT token

### Document Management
- `POST /documents/upload/discharge` - Upload discharge summary PDF
- `POST /documents/upload/bill` - Upload hospital bill PDF
- `GET /documents/` - List all user documents
- `GET /documents/{doc_id}` - Get document with extracted text
- `GET /documents/{doc_id}/word` - Generate and download Word version
- `DELETE /documents/{doc_id}` - Delete document

### Chat (Multi-Agent)
- `POST /chat/` - Ask questions to the multi-agent system

## 🧪 Testing the System

### Test Flow

#### 1. Create User Account
```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "password": "securepass123",
    "full_name": "Test Patient"
  }'
```

#### 2. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/form-data" \
  -F "username=patient@example.com" \
  -F "password=securepass123"
```

Save the `access_token` from the response.

#### 3. Upload Discharge Summary
```bash
curl -X POST "http://localhost:8000/documents/upload/discharge" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@docs/discharge_summaries/discharge_summ_pdf_2.pdf"
```

#### 4. Upload Hospital Bill
```bash
curl -X POST "http://localhost:8000/documents/upload/bill" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@docs/bills/OC_AIIMS_Bill_1.pdf"
```

#### 5. Ask Questions (Multi-Agent Chat)

**Discharge Summary Questions:**
```bash
curl -X POST "http://localhost:8000/chat/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain my diagnosis in simple terms"}'
```

**Bill Validation:**
```bash
curl -X POST "http://localhost:8000/chat/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Check if my hospital bill has any overcharging"}'
```

**Medicine Price Comparison:**
```bash
curl -X POST "http://localhost:8000/chat/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Compare prices for my prescribed medicines"}'
```

**Diet Planning:**
```bash
curl -X POST "http://localhost:8000/chat/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a 7-day meal plan for my condition"}'
```

**Complex Multi-Agent Query:**
```bash
curl -X POST "http://localhost:8000/chat/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain my diagnosis, check my bill for overcharging, and suggest a diet plan"}'
```

### Test with Swagger UI

1. Go to `http://localhost:8000/docs`
2. Click "Authorize" and enter your token
3. Try different endpoints interactively

## 🗂️ Project Structure

```
GIG/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database models (SQLAlchemy)
│   ├── auth/                   # Authentication (JWT)
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── utils.py
│   ├── documents/              # Document upload & processing
│   │   ├── router.py
│   │   ├── processor.py        # OCR + chunking
│   │   └── schemas.py
│   ├── chat/                   # Chat interface
│   │   ├── router.py
│   │   └── orchestrator.py     # Multi-agent supervisor
│   ├── agents/                 # Specialized agents
│   │   ├── base.py             # Base agent class
│   │   ├── discharge_agent.py  # Discharge summary agent
│   │   ├── bill_agent.py       # Bill validator agent
│   │   ├── medicine_agent.py   # Medicine price agent
│   │   └── diet_agent.py       # Diet planning agent
│   ├── vectorstore/            # FAISS vector stores
│   │   ├── store.py            # Vector store management
│   │   └── embeddings.py       # HuggingFace embeddings
│   └── scrapers/               # Web scrapers
│       └── pharmacy.py         # Pharmacy price scraper
├── scripts/
│   └── setup_knowledge_base.py # Index shared documents
├── docs/                       # Sample documents & regulations
│   ├── regulations/            # NPPA, CGHS rates
│   ├── dietary_guide/          # Dietary guidelines
│   ├── insurance_policies/     # Insurance policy PDFs
│   ├── discharge_summaries/    # Sample discharge PDFs
│   └── bills/                  # Sample hospital bills
├── data/
│   ├── healthcare.db           # SQLite database
│   ├── users/                  # User-specific data
│   │   └── {user_id}/
│   │       ├── uploads/        # Uploaded PDFs
│   │       └── faiss_index/    # Per-user vector index
│   └── shared/                 # Shared vector stores
│       ├── regulations_index/
│       ├── dietary_index/
│       └── insurance_index/
├── pdf_to_word.py              # PDF to Word converter
├── requirements.txt
├── .env                        # Environment variables
└── README.md
```

## 🔧 Technology Stack

### Backend
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM with SQLite
- **JWT** - Authentication

### AI/ML
- **Google Gemini 2.5 Flash** - LLM (latest stable model)
- **LangChain Google GenAI** - Multi-agent framework with tool calling
- **HuggingFace (all-MiniLM-L6-v2)** - Embeddings (free, local)
- **FAISS** - Vector database

### Document Processing
- **PyMuPDF (fitz)** - PDF rendering
- **RapidOCR** - OCR for scanned documents
- **python-docx** - Word document generation

### Web Scraping
- **BeautifulSoup4** - HTML parsing
- **Requests** - HTTP client

## 📊 Key Features

### Smart Chunking
- Table-aware chunking (keeps tables intact)
- Context-preserving overlap
- Metadata tagging (year, document type, page number)

### Metadata Filtering
- Filter by year (e.g., "show 2024 discharge summaries")
- Filter by document type (discharge vs bill)
- Filter by filename

### Citations
- Every RAG response includes source citations
- Format: `[1] filename.pdf - Page 5`
- Enables verification and trust

### Multi-Platform Medicine Search
- Parallel scraping of 3 platforms
- Best price identification
- Direct purchase links

### Regulation Compliance
- NPPA ceiling prices (updated Feb 2025)
- CGHS rates (updated Oct 2025)
- Insurance policy validation

## 🎯 Use Cases

1. **Post-Discharge Patient Education**
   - "What does my diagnosis mean?"
   - "How should I take my medicines?"
   - "What are the warning signs I should watch for?"

2. **Bill Verification**
   - "Is my room rent within insurance limits?"
   - "Are any medicines overpriced?"
   - "What's the total overcharge amount?"

3. **Cost Savings**
   - "Where can I buy my medicines cheapest?"
   - "Show me generic alternatives"
   - "Compare prices across pharmacies"

4. **Recovery Support**
   - "What should I eat for diabetes?"
   - "Foods to avoid with my medications"
   - "Create a 7-day meal plan"

## 🐛 Troubleshooting

### Common Issues

**1. "No regulations found"**
- Run `python scripts/setup_knowledge_base.py` to index shared documents

**2. "Medicine prices not found"**
- Check internet connection (scraper needs network access)
- Try using generic medicine names

**3. "Document processing failed"**
- Ensure PDF is not password-protected
- Check if file is a valid PDF

**4. "LLM timeout"**
- Increase timeout in config
- Check Gemini API key validity

## 📝 Notes

- **Demo System**: Designed for demonstration; use appropriate security for production
- **Happy Paths**: Some edge cases are simplified for demo purposes
- **User Isolation**: Each user has a separate vector index
- **Background Processing**: Document processing happens asynchronously

## 🔐 Security Considerations (Production)

- Use HTTPS in production
- Implement rate limiting
- Add input validation and sanitization
- Use proper secret management (not `.env`)
- Implement RBAC if needed
- Add audit logging
- Regular security updates

## 📚 References

- **NPPA**: National Pharmaceutical Pricing Authority
- **CGHS**: Central Government Health Scheme
- **LangChain Multi-Agent**: https://docs.langchain.com/oss/python/langchain/multi-agent/
- **Gemini API**: https://ai.google.dev/

## 👨‍💻 Development

To contribute or extend:
1. Add new agents in `app/agents/`
2. Wrap them as tools in `orchestrator.py`
3. Update routing logic if needed
4. Test with sample documents

## ✅ Testing Checklist

- [ ] Setup knowledge base indexed successfully
- [ ] User signup and login working
- [ ] Upload discharge summary PDF
- [ ] Upload hospital bill PDF
- [ ] Ask discharge summary questions (with citations)
- [ ] Validate bill for overcharging
- [ ] Compare medicine prices (check 3 platforms)
- [ ] Generate diet plan
- [ ] Test complex multi-agent queries
- [ ] Generate Word document from PDF
- [ ] Verify user data isolation

## 📄 License

[Specify your license]

## 🤝 Contact

For questions or support, contact [your email]
