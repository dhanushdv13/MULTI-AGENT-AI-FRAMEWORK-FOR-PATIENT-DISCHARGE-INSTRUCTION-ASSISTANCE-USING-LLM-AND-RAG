from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime
from pymongo.errors import DuplicateKeyError

from app.db.mongo import users
from app.models.user import RegisterUser
from app.core.security import hash_password, verify_password, create_token

router = APIRouter(prefix="/auth", tags=["Auth"])


# -----------------------------
# POST /auth/register
# -----------------------------
@router.post("/register")
async def register(data: RegisterUser):
    try:
        doc = {
            "full_name": data.full_name,
            "username": data.username,
            "email": data.email,
            "mobile": data.mobile,
            "age": data.age,
            "gender": data.gender,
            "address": data.address,
            "password": hash_password(data.password),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        res = await users.insert_one(doc)
        return {"user_id": str(res.inserted_id)}

    except DuplicateKeyError:
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists"
        )


# -----------------------------
# POST /auth/login  (OAuth2)
# -----------------------------
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = await users.find_one({"username": form_data.username})

    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"user_id": str(user["_id"])})
    return {
        "access_token": token,
        "token_type": "bearer"
    }
