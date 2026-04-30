"""
FastAPI dependency: extract and verify the current user from JWT.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from security import decode_jwt
from database import users_col

_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(_oauth2)) -> dict:
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = await users_col().find_one({"_id": ObjectId(payload["user_id"])})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user
