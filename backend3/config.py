"""
Application configuration – reads from backend2/.env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env is in the same directory as this file (backend2/)
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# ── MongoDB ──────────────────────────────────────────────────
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME: str = "medical_db"

# ── JWT ──────────────────────────────────────────────────────
JWT_SECRET: str = os.getenv("JWT_SECRET", "changeme")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = 60

# ── CORS ─────────────────────────────────────────────────────
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",")]

# ── AI / Embeddings ──────────────────────────────────────────
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── File-system paths ────────────────────────────────────────
BASE_DIR: Path = Path(__file__).resolve().parent   # backend2/
UPLOADS_DIR: Path = BASE_DIR / "data" / "uploads"
VECTORSTORES_DIR: Path = BASE_DIR / "vectorstores"

# Ensure runtime directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
VECTORSTORES_DIR.mkdir(parents=True, exist_ok=True)
