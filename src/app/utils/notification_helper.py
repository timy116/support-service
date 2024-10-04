import base64
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Union

import requests
from fastapi import status, BackgroundTasks
from starlette.datastructures import CommaSeparatedStrings
from requests import Response
from structlog import get_logger, BoundLogger

from app.core.config import settings
from app.core.enums import (
    NotificationCategories,
    LineApis,
    NotificationTypes,
    LogLevel,
    LineNotifyErrorMessages,
)
from app.models.notifications import Notification
from app.utils.email_processors import GmailProcessor

logger: BoundLogger = get_logger()


class NotificationStrategy(ABC):
    """
    Abstract base class for notification strategies.
    This class defines the interface for sending notifications.
    Subclasses must implement the `send` method to provide specific notification sending behavior.
    """

    @abstractmethod
    def send(self, notification: Notification) -> bool:
        """
        Sends a notification.
        :param notification: The notification to send.
        :return: True if the notification was sent successfully, False otherwise.
        """
        pass


class EmailNotificationStrategy(NotificationStrategy):
    """
    A concrete implementation of the `NotificationStrategy` interface that sends notifications via email.
    """

    def __init__(self, recipient: Union[CommaSeparatedStrings, None] = None, subject: str = ""):
        self.mail_processor = GmailProcessor()
        self.recipients: CommaSeparatedStrings = recipient or CommaSeparatedStrings(settings.SERVICE_RECIPIENTS)
        self.subject: str = subject

    @property
    def recipients(self):
        return self._recipients

    @recipients.setter
    def recipients(self, value: CommaSeparatedStrings):
        self._recipients = value

    @property
    def subject(self):
        return self._subject

    @subject.setter
    def subject(self, value):
        self._subject = value

    def send(self, notification: Notification) -> bool:
        for recipient in self._recipients:
            email_message = MIMEMultipart()
            email_message['to'] = recipient
            email_message['subject'] = self.subject
            email_message.attach(MIMEText(notification.message, 'plain'))

            raw_message = base64.urlsafe_b64encode(email_message.as_bytes()).decode('utf-8')
            try:
                self.mail_processor.service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
            except Exception as e:
                logger.exception(f"An error occurred while sending email: {e}")
                return False

        return True

    def send_system_notify(self, notification: Notification) -> bool:
        copy_notification = notification.model_copy(
            update={
                "category": NotificationCategories.SYSTEM,
                "type": NotificationTypes.EMAIL,
                "level": LogLevel.ERROR,
            }
        )

        # Save the system notification to the database
        BackgroundTasks().add_task(copy_notification.save)

        return self.send(copy_notification)


class LineNotificationStrategy(NotificationStrategy):
    """
    A concrete implementation of the `NotificationStrategy` interface that sends notifications via LINE NOTIFY.
    """

    def __init__(self):
        self.mail_strategy = EmailNotificationStrategy()

    @staticmethod
    def get_headers(token: str):
        return {
            "Authorization": f"Bearer {token}",
        }

    def _send_notify(self, notification: Notification) -> Response:
        """
        Sends a LINE notification using the LINE Notify API.

        :param notification: The notification to send.
        :return: The response from the LINE Notify API.
        """

        return requests.post(
            LineApis.NOTIFY,
            headers=self.get_headers(
                settings.SERVICE_NOTIFY_TOKEN
                if notification.category is NotificationCategories.SERVICE
                else settings.SYSTEM_NOTIFY_TOKEN
            ),
            data={"message": notification.message},
        )

    def send(self, notification: Notification) -> bool:
        """
        Sends a LINE notification.
        If the notification fails to send or an error occurs, a system notification will be sent via email.

        :param notification: The notification to send.
        :return: True if the notification was sent successfully, False otherwise.
        """

        try:
            resp = self._send_notify(notification)

            # If the response status code is not 200, send a system notification via email
            if resp.status_code != status.HTTP_200_OK:
                subject = LineNotifyErrorMessages.SEND_MESSAGE_FAILED
                msg = f"{subject}: {resp.text}"
                logger.error(msg)

                return self._send_system_notify(subject, notification, msg)

            return True
        except Exception as e:
            subject = LineNotifyErrorMessages.ERROR_OCCURRED
            logger.exception(subject)
            msg = f"{subject}: {e}"

            return self._send_system_notify(subject, notification, msg)

    def _send_system_notify(self, subject: str, notification: Notification, msg: str):
        self.mail_strategy.subject = subject
        self.mail_strategy.recipients = CommaSeparatedStrings(settings.SYSTEM_RECIPIENTS)
        self.mail_strategy.send_system_notify(notification.model_copy(update={"message": msg}))

        return False


class NotificationManager:
    """
    NotificationManager is a class that manages the sending of notifications.
    It delegates the actual sending of notifications to a concrete `NotificationStrategy` object.
    """

    def __init__(self, strategy: NotificationStrategy):
        self.strategy = strategy

    def send_notification(self, notification: Notification) -> bool:
        return self.strategy.send(notification)
