from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from app.core.enums import NotificationCategories, LogLevel, NotificationTypes
from app.models import Notification
from app.utils.datetime import datetime_formatter


async def test_get_notifications_with_invalid_date(client: TestClient):
    # Act
    result = client.get(
        url="/api/v1/notifications",
        params={
            "date": "invalid date"
        }
    )

    # Assert
    assert result.status_code == 400


@pytest.mark.asyncio
async def test_get_notifications(
        init_db,
        mock_notifications: list[Notification],
        client: TestClient
):
    # Arrange
    await Notification.insert_many(mock_notifications)

    # Act
    # Case 1: params with specify date
    result = client.get(
        url="/api/v1/notifications",
        params={
            "date": "20241009"
        }
    )

    # Assert
    assert result.status_code == 200
    assert result.json()["total"] == 2

    # Case 2: params with category
    result = client.get(
        url="/api/v1/notifications",
        params={
            "category": NotificationCategories.SYSTEM
        }
    )

    # Assert
    assert result.status_code == 200
    assert result.json()["total"] == 4

    # Case 3: params with level
    result = client.get(
        url="/api/v1/notifications",
        params={
            "level": LogLevel.INFO
        }
    )

    # Assert
    assert result.status_code == 200
    assert result.json()["total"] == 1


@pytest.mark.asyncio
@patch("app.dependencies.notifications.correlation_id", new_callable=MagicMock)
async def test_create_notification(mock_correlation_id, init_db, client: TestClient):
    # Arrange
    mock_correlation_id.get.return_value = uuid4().hex
    dt = "2024-10-09"
    notification_instance = Notification(
        date=datetime_formatter(dt),
        correlation_id=mock_correlation_id.get(),
        category=NotificationCategories.SYSTEM,
        type=NotificationTypes.LINE,
        level=LogLevel.ERROR,
        message="Test error message",
    )

    # Act
    result = client.post(
        url="/api/v1/notifications",
        json={
            "date": dt,
            "category": notification_instance.category,
            "type": notification_instance.type,
            "level": notification_instance.level,
            "message": notification_instance.message
        }
    )

    # Assert
    assert result.status_code == 201
    assert result.json()["correlation_id"] == str(notification_instance.correlation_id)
    assert result.json()["created_at"] is not None
    assert result.json()["date"] == dt
    assert result.json()["category"] == notification_instance.category
    assert result.json()["type"] == notification_instance.type
    assert result.json()["level"] == notification_instance.level
    assert result.json()["message"] == notification_instance.message
    assert await Notification.find_all().count() == 1
    assert (await Notification.find_all().first_or_none()).correlation_id == notification_instance.correlation_id
