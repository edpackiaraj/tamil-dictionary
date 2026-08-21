from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://tamildict:tamildict_secret@localhost:5432/tamildict"
    secret_key: str = "change_this_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    cors_origins: list[str] = ["*"]
    app_name: str = "Tamil Dictionary API"
    version: str = "1.0.0"

    class Config:
        env_file = ".env"

settings = Settings()
