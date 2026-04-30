"""
Async MongoDB connection via Motor.
"""
from motor.motor_asyncio import AsyncIOMotorClient
import config

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(config.MONGO_URI)
    return _client


def get_db():
    return get_client()[config.DB_NAME]


def users_col():
    return get_db()["users"]


def documents_col():
    return get_db()["documents"]


async def create_indexes():
    """Create unique indexes on startup."""
    col = users_col()
    await col.create_index("email", unique=True)
    await col.create_index("username", unique=True)
