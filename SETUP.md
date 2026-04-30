# Discharge Agent - Setup Guide

## Prerequisites

- Python 3.12+
- Node.js 18+
- MongoDB (local or Atlas)
- Git

## MongoDB Setup
 Local MongoDB
1. **Install MongoDB** from https://www.mongodb.com/try/download/community
2. **Start MongoDB service**:
   - Windows: MongoDB runs as a service automatically
   - Mac/Linux: `sudo systemctl start mongod`
3. **Connection string**: `mongodb://localhost:27017` (use in `MONGO_URI`)
4. Install MongoDB Compass from https://www.mongodb.com/try/download/compass
### Important Notes

- ✅ **No manual database/collection creation needed!** The application automatically creates:
  - Database: `discharge_agent` (or your specified name)
  - Collections: `users`, `uploads`, `chat_sessions`
  - Indexes: Created automatically on first run
- The backend uses MongoDB's auto-creation feature, so just provide the connection string and start the app!

## Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv backendenv
   ```

3. **Activate virtual environment**
   - Windows: `backendenv\Scripts\activate`
   - Mac/Linux: `source backendenv/bin/activate`

4. **Install dependencies**
   ```bash
   uv pip install -r app/requirements.txt
   ```

5. **Create `.env` file** in `backend/` directory with:
   ```env
   # MongoDB Configuration
   MONGO_URI=mongodb://localhost:27017
   # OR for MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/
   
   # Security
   JWT_SECRET=your-secret-key-here-generate-a-random-string
   
   # AI/LLM Configuration
   LLM_PROVIDER=gemini
   GOOGLE_API_KEY=your_google_api_key_here
   GEMINI_MODEL=gemini-2.0-flash-exp
   
   # Embeddings
   EMBEDDING_MODEL=all-MiniLM-L6-v2
   
   # CORS (Frontend URLs)
   ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```

6. **Run the backend**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   On first run, you'll see logs indicating database and collection creation.

## Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Create `.env.local` file** in `frontend/` directory with:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Run the frontend**
   ```bash
   npm run dev
   ```

## Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
discharge_agent/
├── backend/          # FastAPI backend with AI agents
├── frontend/         # Next.js frontend
└── GIG/             # Reference implementation (alternative architecture)
```

## Troubleshooting

### MongoDB Connection Issues
- Verify your `MONGO_URI` connection string is correct in `.env` file
- Check if MongoDB service is running (for local setup)
- Ensure your IP is whitelisted in Atlas (for cloud setup)
- Database and collections are created automatically on first run

### Missing Dependencies
- Make sure you're in the virtual environment before installing
- Try `pip install --upgrade pip` if installation fails
