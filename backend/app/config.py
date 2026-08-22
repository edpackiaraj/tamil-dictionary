from pydantic_settings import BaseSettings
from pydantic import Field, validator

class Settings(BaseSettings):
    # Database URL can be provided via DATABASE_URL env var (e.g., Railway). Fallback to local dev DB.
    database_url: str = Field(
        default="postgresql+asyncpg://tamildict:tamildict_secret@localhost:5432/tamildict",
        env="DATABASE_URL",
    )
    secret_key: str = "change_this_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    cors_origins: list[str] = ["*"]
    app_name: str = "Tamil Dictionary API"
    version: str = "1.0.0"

    class Config:
        env_file = ".env"

    @validator("database_url", pre=True)
    def ensure_async_driver(cls, v: str) -> str:
        # Railway may supply a plain postgresql:// URL; ensure asyncpg driver is used.
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

settings = Settings()
