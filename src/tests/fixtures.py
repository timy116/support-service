import json
from datetime import datetime
from os.path import dirname, join, abspath
import pytest
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from app.models import SpecialHoliday, DailyReport, Notification

BASE_DIR = dirname(abspath(__file__))


@pytest.fixture
async def init_db():
    client = AsyncMongoMockClient()
    await init_beanie(database=client.db, document_models=[SpecialHoliday, DailyReport, Notification])


@pytest.fixture
def special_holidays():
    holidays = []
    with open(join(f'{BASE_DIR}/utils/data/special_holidays.json'), encoding='utf8') as f:
        data = json.load(f)

    for d in data:
        holidays.extend(
            datetime.strptime(
                holiday['date']['$date'], '%Y-%m-%dT%H:%M:%SZ'
            ).date()
            for holiday in d['holidays']
        )
    return holidays
