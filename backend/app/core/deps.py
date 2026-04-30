from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from app.db.mongo import users
from app.core.security import decode_token

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def current_user(token: str = Depends(oauth2)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    user = await users.find_one({"_id": ObjectId(payload["user_id"])})
    if not user:
        raise HTTPException(401, "User not found")

    return user
