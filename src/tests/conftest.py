from starlette.config import environ

# set test config
environ["UVICORN_HOST"] = "localhost"
environ["UVICORN_PORT"] = "8000"
environ["MONGODB_URI"] = "mongodb://test:test@localhost"
environ["MONGODB_DB_NAME"] = "test"
environ["REDIS_URI"] = "redis://localhost"

from .fixtures import *


@pytest.fixture
def anyio_backend():
    return 'asyncio'
