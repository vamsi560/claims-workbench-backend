from app.config import get_settings

settings = get_settings()

# SQLAlchemy code removed for Retool migration
# If you need database access, implement Retool API calls here

async def get_db():
    raise NotImplementedError("Database access is disabled. Use Retool API instead.")
