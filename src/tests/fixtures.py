import pytest
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from app.models import SpecialHoliday, DailyReport, Notification


@pytest.fixture
async def init_db():
    client = AsyncMongoMockClient()
    await init_beanie(database=client.db, document_models=[SpecialHoliday, DailyReport, Notification])
