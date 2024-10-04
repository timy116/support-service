from datetime import datetime
from uuid import uuid4, UUID

import pytest

from app.core.enums import NotificationCategories, NotificationTypes, LogLevel
from app.models.notifications import Notification
from app.utils.datetime import get_date


@pytest.fixture
def test_data() -> list[Notification]:
    dt = get_date().replace(month=10, day=4)
    correlation_id = uuid4()

    return [
        Notification(
            date=dt,
            correlation_id=correlation_id,
            category=NotificationCategories.SYSTEM,
            type=NotificationTypes.LINE,
            level=LogLevel.ERROR,
            message="Test error message",
        ),
        Notification(
            date=dt,
            correlation_id=correlation_id,
            category=NotificationCategories.SYSTEM,
            type=NotificationTypes.LINE,
            level=LogLevel.ERROR,
            message="Test error message on the same correlation id",
        ),
        Notification(
            date=dt.replace(month=9, day=15),
            correlation_id=uuid4(),
            category=NotificationCategories.SERVICE,
            type=NotificationTypes.LINE,
            level=LogLevel.INFO,
            message="Service message",
        ),
        Notification(
            date=dt.replace(month=9, day=15),
            correlation_id=uuid4(),
            category=NotificationCategories.SERVICE,
            type=NotificationTypes.EMAIL,
            level=LogLevel.INFO,
            message="Service message with email type",
        ),
    ]


@pytest.mark.asyncio
async def test_create_instance_into_db(init_db):
    # Arrange
    # Case 1: Test with valid data
    correlation_id = uuid4()
    message = "Test error message"
    notification = Notification(
        correlation_id=correlation_id,
        category=NotificationCategories.SYSTEM,
        type=NotificationTypes.LINE,
        level=LogLevel.ERROR,
        message=message,
    )

    # Act
    instance = await Notification.insert_one(notification)

    # Assert
    assert instance.correlation_id == notification.correlation_id
    assert instance.category == notification.category
    assert instance.type == notification.type
    assert instance.level == notification.level
    assert instance.message == notification.message
    assert instance.created_at == notification.created_at


@pytest.mark.asyncio
async def test_query_data(init_db, test_data):
    # Arrange
    dt1 = test_data[0].date
    correlation_id = test_data[0].correlation_id
    await Notification.insert_many(test_data)

    # Act
    notifications = await Notification.find_many(Notification.date == dt1).to_list()

    # Assert
    assert len(notifications) == 2
    assert notifications[0].correlation_id == correlation_id
    assert notifications[1].correlation_id == correlation_id

    # Case 2: Test with different date
    dt2 = test_data[2].date
    correlation_id = test_data[2].correlation_id

    # Act
    notifications = await Notification.find_many(Notification.date == dt2).to_list()

    # Assert
    assert len(notifications) == 2
    assert notifications[0].correlation_id == correlation_id
    assert notifications[1].correlation_id != correlation_id

    # Case 3: Test with different notification type
    notification = test_data[3]

    # Act
    notifications = await Notification.find_many(Notification.type == notification.type).to_list()

    # Assert
    assert len(notifications) == 1
    assert notifications[0].type == notification.type

    # Case 4: Test with different category
    notifications = await Notification.find_many(Notification.category == NotificationCategories.SERVICE).to_list()

    # Assert
    assert len(notifications) == 2
    assert notifications[0].category == NotificationCategories.SERVICE

    # Case 5: Test with different level
    notifications = await Notification.find_many(Notification.level == LogLevel.INFO).to_list()

    # Assert
    assert len(notifications) == 2
    assert notifications[0].level == LogLevel.INFO

    # Case 6: Test with different correlation id
    correlation_id = test_data[0].correlation_id

    # Act
    notifications = await Notification.find_many(Notification.correlation_id == correlation_id).to_list()

    # Assert
    assert len(notifications) == 2


@pytest.mark.asyncio
async def test_create_from_exception(init_db):
    # Arrange
    # Case 1: Test with valid data
    correlation_id = str(uuid4())
    message = "Test error message"

    # Act
    notification = await Notification.create_from_exception(correlation_id, message)

    # Assert
    assert isinstance(notification.correlation_id, UUID)
    assert str(notification.correlation_id) == correlation_id
    assert notification.category == NotificationCategories.SYSTEM
    assert notification.type == NotificationTypes.LINE
    assert notification.level == LogLevel.ERROR
    assert notification.message == message
    assert isinstance(notification.created_at, datetime)

    # Case 2: Test with different notification type
    correlation_id = str(uuid4())
    notification_type = NotificationTypes.EMAIL
    notification = await Notification.create_from_exception(correlation_id, message, notification_type)

    assert notification.type == notification_type

    # Case 3: Test with invalid correlation id
    correlation_id = "invalid-uuid"
    message = "Test error message"
    with pytest.raises(ValueError):
        await Notification.create_from_exception(correlation_id, message)
