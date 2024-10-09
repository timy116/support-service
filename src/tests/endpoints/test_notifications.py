import pytest
from starlette.testclient import TestClient

from app.core.enums import NotificationCategories, LogLevel
from app.models import Notification


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
