
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "")
JWT_SECRET = os.getenv("JWT_SECRET", "secret")
JWT_ALGO = "HS256"

# CORS Settings
_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
if _origins.startswith("["):
     # Handle JSON array string if provided
    import json
    try:
        ALLOWED_ORIGINS = json.loads(_origins)
    except:
        ALLOWED_ORIGINS = ["*"]
else:
    ALLOWED_ORIGINS = [i.strip() for i in _origins.split(",")]

# AI Settings
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LLM_MODEL = "gemini-2.5-flash"
LLM_TEMPERATURE = 0.3

# Embeddings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Document Processing
OCR_DPI = 300
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
USERS_DIR = DATA_DIR / "users"
VECTORS_DIR = DATA_DIR / "vectors"
SHARED_DIR = DATA_DIR / "shared"