import json
from datetime import datetime
from os.path import dirname, join, abspath
from unittest.mock import MagicMock, patch

import pytest
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from app.core.config import Settings
from app.models import SpecialHoliday, DailyReport, Notification

BASE_DIR = dirname(abspath(__file__))


###################
# Global fixtures #
###################
@pytest.fixture(scope="module", autouse=True)
def mock_settings():
    mock_settings = MagicMock(spec=Settings)
    mock_settings.SYSTEM_RECIPIENTS = "admin@example.com,"
    mock_settings.SERVICE_RECIPIENTS = "test@example.com,"
    mock_settings.SERVICE_NOTIFY_TOKEN = "service_token"
    mock_settings.SYSTEM_NOTIFY_TOKEN = "system_token"

    return mock_settings


@pytest.fixture(autouse=True)
def mock_settings_globally(mock_settings):
    with patch("app.utils.notification_helper.settings", mock_settings):
        yield


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
