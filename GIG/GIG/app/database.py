"""
Database Configuration and Models
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

from app.config import settings


# Create async engine for SQLite — echo=False to keep terminal clean
ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)

# Sync engine for migrations — echo=False
sync_engine = create_engine(settings.DATABASE_URL, echo=False)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


class DocumentType(str, enum.Enum):
    """Document type enumeration."""
    DISCHARGE = "discharge"
    BILL = "bill"


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")


class Document(Base):
    """Document model for uploaded PDFs."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    doc_type = Column(SQLEnum(DocumentType), nullable=False)
    file_path = Column(String(512), nullable=False)
    extracted_text = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Integer, default=0)  # 0=pending, 1=done, -1=failed
    
    # Relationships
    owner = relationship("User", back_populates="documents")


async def init_db():
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
