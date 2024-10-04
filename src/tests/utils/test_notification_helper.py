from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest
from starlette.datastructures import CommaSeparatedStrings

from app.core.enums import (
    NotificationCategories,
    NotificationTypes,
    LogLevel,
    LineApis,
    LineNotifyErrorMessages,
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


class TestLineNotificationStrategy:
    @patch('app.utils.notification_helper.requests.post')
    def test_send_success(self, mock_post, notification, mock_settings):
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        strategy = LineNotificationStrategy()
        headers = strategy.get_headers(mock_settings.SERVICE_NOTIFY_TOKEN)
        data = {"message": notification.message}

        # Act
        result = strategy.send(notification)

        # Assert
        assert result == True
        mock_post.assert_called_once_with(LineApis.NOTIFY, headers=headers, data=data)

    @patch('app.utils.notification_helper.requests.post')
    @patch(
        'app.utils.notification_helper.EmailNotificationStrategy',
        new_callable=MagicMock(spec=EmailNotificationStrategy)
    )
    def test_send_failure(self, mock_email_strategy, mock_post, notification, mock_settings):
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_post.return_value = mock_response
        mock_email_strategy.return_value.send_system_notify.return_value = True
        strategy = LineNotificationStrategy()
        mail_subject = LineNotifyErrorMessages.SEND_MESSAGE_FAILED
        msg = f"{mail_subject}: {mock_response.text}"
        copy_notification = notification.model_copy(update={"message": msg})

        # Act
        result = strategy.send(notification)

        # Assert
        assert result == False
        assert strategy.mail_strategy.subject == mail_subject
        assert list(strategy.mail_strategy.recipients) == list(CommaSeparatedStrings(mock_settings.SYSTEM_RECIPIENTS))
        mock_post.assert_called_once()
        mock_email_strategy.return_value.send_system_notify.assert_called_once_with(copy_notification)

    @patch('app.utils.notification_helper.requests.post')
    @patch(
        'app.utils.notification_helper.EmailNotificationStrategy',
        new_callable=MagicMock(spec=EmailNotificationStrategy)
    )
    def test_send_exception(self, mock_email_strategy, mock_post, notification, mock_settings):
        # Arrange
        error_msg = "Test error"
        mock_post.side_effect = Exception(error_msg)
        mock_email_strategy.return_value.send_system_notify.return_value = True
        strategy = LineNotificationStrategy()
        mail_subject = LineNotifyErrorMessages.ERROR_OCCURRED
        msg = f"{mail_subject}: {error_msg}"
        copy_notification = notification.model_copy(update={"message": msg})

        # Act
        result = strategy.send(notification)

        # Assert
        assert result == False
        mock_post.assert_called_once()
        assert strategy.mail_strategy.subject == mail_subject
        mock_email_strategy.return_value.send_system_notify.assert_called_once_with(copy_notification)


class TestNotificationManager:
    def test_send_notification(self, notification, mock_settings):
        # Arrange
        mock_strategy = MagicMock()
        mock_strategy.send.return_value = True
        manager = NotificationManager(mock_strategy)

        # Act
        result = manager.send_notification(notification)

        # Assert
        assert result == True
        mock_strategy.send.assert_called_once_with(notification)
