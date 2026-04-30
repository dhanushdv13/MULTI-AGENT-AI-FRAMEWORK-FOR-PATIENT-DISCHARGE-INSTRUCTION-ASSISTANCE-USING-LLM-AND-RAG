from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.core import config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    # bcrypt works on bytes and max 72 bytes
    password_bytes = password.encode("utf-8")
    return pwd_context.hash(password_bytes)


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
