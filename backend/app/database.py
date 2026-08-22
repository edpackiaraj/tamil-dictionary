import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Simple console logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure asyncpg driver in DB URL
db_url = settings.database_url
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
logger.info(f"Connecting to database using URL: {db_url}")

from sqlalchemy.pool import NullPool

# Engine with NullPool for robust connectivity
engine = create_async_engine(
    db_url,
    echo=False,
    poolclass=NullPool,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
