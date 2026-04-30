from motor.motor_asyncio import AsyncIOMotorClient
from app.core import config

client = AsyncIOMotorClient(config.MONGO_URI)
db = client.medical_db

users = db.users
uploads = db.uploads
chat_history = db.chat_history