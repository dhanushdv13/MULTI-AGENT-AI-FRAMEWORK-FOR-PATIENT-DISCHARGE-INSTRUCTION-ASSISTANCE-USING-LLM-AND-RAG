from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class RegisterUser(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    mobile: str
    age: int
    gender: str
    address: Optional[str] = None
    password: str

class UserOut(BaseModel):
    id: str
    full_name: str
    username: str
    email: EmailStr
    mobile: str
    age: int
    gender: str
    address: Optional[str]
    created_at: datetime
