"""
Auth router: /auth/register and /auth/login
"""
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from features.auth.schemas import RegisterRequest, RegisterResponse, TokenResponse
from features.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])
_svc = AuthService()


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(req: RegisterRequest):
    return await _svc.register(req)


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    return await _svc.login(form.username, form.password)
