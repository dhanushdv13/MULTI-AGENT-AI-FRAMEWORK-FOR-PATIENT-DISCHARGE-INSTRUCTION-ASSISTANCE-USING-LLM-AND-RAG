"""
Password hashing and JWT utilities.
"""
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
import config

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Passwords ─────────────────────────────────────────────────

def hash_pw(plain: str) -> str:
    return _pwd_ctx.hash(plain.encode("utf-8"))


def verify_pw(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain.encode("utf-8"), hashed)


# ── JWT ───────────────────────────────────────────────────────

def sign_jwt(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=config.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except JWTError:
        return None
