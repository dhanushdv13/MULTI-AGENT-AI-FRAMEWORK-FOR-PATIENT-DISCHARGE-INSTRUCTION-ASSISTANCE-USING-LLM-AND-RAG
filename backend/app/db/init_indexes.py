async def create_indexes(db):
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True)
    await db.uploads.create_index("user_id")
    await db.uploads.create_index("vector_status")
