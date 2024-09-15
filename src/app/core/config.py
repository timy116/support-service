from typing import List, Annotated

from pydantic import UrlConstraints
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

# This adds support for 'mongodb+srv' connection schemas when using e.g. MongoDB Atlas
MongoDsn = Annotated[
    MultiHostUrl,
    UrlConstraints(
        allowed_schemes=["mongodb", "mongodb+srv"],
        default_port=27017,
    ),
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8', case_sensitive=True, extra='allow'
    )

    # Application
    PROJECT_NAME: str = "SUPPORT SERVICE"
    PROJECT_VERSION: str = "0.1.0"
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

    # Redis
    REDIS_URI: str


settings = Settings()
