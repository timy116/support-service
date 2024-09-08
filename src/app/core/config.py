import secrets
from typing import List

from pydantic_settings import BaseSettings
from pydantic import EmailStr, MongoDsn

from src import __version__

# This adds support for 'mongodb+srv' connection schemas when using e.g. MongoDB Atlas
MongoDsn.allowed_schemes.add("mongodb+srv")


class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "support_service"
    PROJECT_VERSION: str = __version__
    API_V1_STR: str = "v1"
    DEBUG: bool = True

    # CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000"]'
    CORS_ORIGINS: List[str] = []
    USE_CORRELATION_ID: bool = True

    UVICORN_HOST: str
    UVICORN_PORT: int

    # MongoDB
    MONGODB_URI: MongoDsn
    MONGODB_DB_NAME: str

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
