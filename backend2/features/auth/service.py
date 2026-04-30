"""
Auth service: registration and login logic.
"""
from fastapi import HTTPException, status
from bson import ObjectId
from database import users_col
from security import hash_pw, verify_pw, sign_jwt
from features.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, RegisterResponse


class AuthService:

    async def register(self, req: RegisterRequest) -> RegisterResponse:
        existing = await users_col().find_one({"email": req.email})
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        existing_username = await users_col().find_one({"username": req.username})
        if existing_username:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

        result = await users_col().insert_one({
            "username": req.username,
            "email": req.email,
            "hashed_password": hash_pw(req.password),
        })
        return RegisterResponse(message="User registered successfully", user_id=str(result.inserted_id))

    async def login(self, username: str, password: str) -> TokenResponse:
        user = await users_col().find_one({"username": username})
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        # Support both field names: "hashed_password" (new) and "password" (old backend)
        stored_hash = user.get("hashed_password") or user.get("password")
        if not stored_hash or not verify_pw(password, stored_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = sign_jwt(str(user["_id"]))
        return TokenResponse(access_token=token)
