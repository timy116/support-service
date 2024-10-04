import pytest

from uuid import uuid4, UUID
from unittest.mock import patch, MagicMock

from fastapi import BackgroundTasks
from starlette.datastructures import CommaSeparatedStrings

from app.core.enums import (
    NotificationCategories,
    NotificationTypes,
    LogLevel,
)
from app.models.notifications import Notification
from app.utils.notification_helper import (
    EmailNotificationStrategy,
    LineNotificationStrategy,
    NotificationManager,
)


@pytest.fixture
def notification(init_db):
    return Notification(
        correlation_id=uuid4(),
        category=NotificationCategories.SERVICE,
        type=NotificationTypes.EMAIL,
        level=LogLevel.INFO,
        message="Test message"
    )


class TestEmailNotificationStrategy:
    @patch('app.utils.notification_helper.GmailProcessor')
    def test_send(self, mock_gmail_processor, notification, mock_settings):
        # Arrange
        mock_service = MagicMock()
        mock_gmail_processor.return_value.service = mock_service
        strategy = EmailNotificationStrategy()

        # Act
        result = strategy.send(notification)

        # Assert
        assert strategy.recipients is not None
        assert isinstance(strategy.recipients, CommaSeparatedStrings)
        assert result == True
        mock_service.users().messages().send.assert_called_once()

    @patch('app.utils.notification_helper.GmailProcessor')
    def test_send_failure(self, mock_gmail_processor, notification, mock_settings):
        # Arrange
        mock_service = MagicMock()
        mock_service.users().messages().send.side_effect = Exception("Test error")
        mock_gmail_processor.return_value.service = mock_service
        strategy = EmailNotificationStrategy()

        # Act
        result = strategy.send(notification)

        # Assert
        assert result == False

    @patch('app.utils.notification_helper.BackgroundTasks')
    @patch('app.utils.notification_helper.GmailProcessor')
    def test_send_system_notify(self, mock_gmail_processor, mock_background_tasks, notification, mock_settings):
        # Arrange
        mock_service = MagicMock()
        mock_gmail_processor.return_value.service = mock_service
        strategy = EmailNotificationStrategy()

        # Act
        result = strategy.send_system_notify(notification)

        # Assert
        assert result == True
        mock_background_tasks.return_value.add_task.assert_called_once()
        mock_service.users().messages().send.assert_called_once()
