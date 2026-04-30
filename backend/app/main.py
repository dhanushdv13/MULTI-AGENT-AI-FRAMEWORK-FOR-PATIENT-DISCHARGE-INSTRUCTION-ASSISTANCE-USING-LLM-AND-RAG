from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, uploads, chat
from app.db.mongo import db
from app.db.init_indexes import create_indexes

app = FastAPI(
    title="Medical Backend API",
    version="1.0",
    description="Auth, Uploads, ML-ready APIs"
)

# Configure CORS
from app.core import config

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await create_indexes(db)

app.include_router(auth.router)
app.include_router(uploads.router)
app.include_router(chat.router)
