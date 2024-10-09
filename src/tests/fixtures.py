import json
from datetime import datetime
from os.path import dirname, join, abspath
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4

import pytest
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient
from starlette.testclient import TestClient

from app.core.config import Settings
from app.core.enums import Category, SupplyType, ProductType, NotificationCategories, NotificationTypes, LogLevel, \
    DailyReportHttpErrors
from app.dependencies.redis import get_redis, Redis
from app.models import SpecialHoliday, DailyReport, Notification
from app.models.daily_reports import Product
from app.utils.datetime import get_date, datetime_formatter

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


@pytest.fixture(scope="module")
@patch("app.main.StaticFiles", new_callable=MagicMock, auto_use=True)
def test_app(mock_static_files, mock_settings):
    mock_redis = AsyncMock(spec=Redis)

    async def override_get_redis():
        return mock_redis

    from app.main import create_app
    app = create_app()
    app.dependency_overrides[get_redis] = override_get_redis

    return app, mock_redis


@pytest.fixture(scope="module")
def client(test_app):
    app, _ = test_app

    return TestClient(app)


@pytest.fixture
def mock_daily_reports() -> list[DailyReport]:
    date = get_date().replace(month=9, day=11)

    return [
        DailyReport(
            date=date,
            category=Category.AGRICULTURE,
            supply_type=SupplyType.ORIGIN,
            product_type=ProductType.CROPS,
            products=[
                Product(date=date, product_name="香蕉", average_price=10.0),
                Product(date=date, product_name="芒果", average_price=15.3)
            ]
        ),
        DailyReport(
            date=date,
            category=Category.AGRICULTURE,
            supply_type=SupplyType.WHOLESALE,
            product_type=ProductType.CROPS,
            products=[
                Product(date=date, product_name="香蕉", average_price=10.0),
                Product(date=date, product_name="芒果", average_price=15.3)
            ]
        ),
        DailyReport(
            date=date.replace(day=5),
            category=Category.FISHERY,
            supply_type=SupplyType.ORIGIN,
            product_type=ProductType.SEAFOOD,
            products=[
                Product(date=date, product_name="吳郭魚", average_price=30.5),
            ]
        ),
        DailyReport(
            date=date.replace(day=5),
            category=Category.FISHERY,
            supply_type=SupplyType.WHOLESALE,
            product_type=ProductType.SEAFOOD,
            products=[
                Product(date=date, product_name="白蝦", average_price=100.3)
            ]
        ),
    ]


@pytest.fixture
def mock_notifications() -> list[Notification]:
    return [
        Notification(
            date=datetime_formatter("20241009"),
            correlation_id=uuid4(),
            category=NotificationCategories.SYSTEM,
            type=NotificationTypes.LINE,
            level=LogLevel.ERROR,
            message=DailyReportHttpErrors.FAILED.value,
            created_at=datetime.now()
        ),
        Notification(
            date=datetime_formatter("20241009"),
            correlation_id=uuid4(),
            category=NotificationCategories.SYSTEM,
            type=NotificationTypes.LINE,
            level=LogLevel.ERROR,
            message=DailyReportHttpErrors.FAILED.value,
            created_at=datetime.now()
        ),
        Notification(
            date=datetime_formatter("20241008"),
            correlation_id=uuid4(),
            category=NotificationCategories.SYSTEM,
            type=NotificationTypes.EMAIL,
            level=LogLevel.ERROR,
            message=DailyReportHttpErrors.INTERNAL_SERVER_ERROR.value,
            created_at=datetime.now()
        ),
        Notification(
            date=datetime_formatter("20241007"),
            correlation_id=uuid4(),
            category=NotificationCategories.SYSTEM,
            type=NotificationTypes.EMAIL,
            level=LogLevel.ERROR,
            message=DailyReportHttpErrors.INTERNAL_SERVER_ERROR.value,
            created_at=datetime.now()
        ),
        Notification(
            date=datetime_formatter("20241007"),
            correlation_id=uuid4(),
            category=NotificationCategories.SERVICE,
            type=NotificationTypes.LINE,
            level=LogLevel.INFO,
            message="",
            created_at=datetime.now()
        ),
    ]
