"""
Authentication Router - Signup, Login, Me endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from pathlib import Path

from app.database import get_db, User
from app.config import settings
from app.auth.schemas import UserCreate, UserResponse, Token, UserLogin
from app.auth.utils import (
    get_password_hash,
    create_access_token,
    authenticate_user,
    get_current_user,
    get_user_by_email,
)


router = APIRouter()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if email exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create user directories
    user_dir = settings.USERS_DIR / str(new_user.id)
    (user_dir / "uploads" / "discharge").mkdir(parents=True, exist_ok=True)
    (user_dir / "uploads" / "bills").mkdir(parents=True, exist_ok=True)
    (user_dir / "faiss_index").mkdir(parents=True, exist_ok=True)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password (form data for Swagger UI)."""
    user = await authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires,
    )
    
    return Token(access_token=access_token)


@router.post("/login/json", response_model=Token)
async def login_json(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login with JSON body (for frontend)."""
    user = await authenticate_user(db, user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires,
    )
    
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's profile."""
    return current_user
