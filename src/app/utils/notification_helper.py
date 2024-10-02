import base64
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from structlog import get_logger, BoundLogger

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

    def __init__(self, recipient: list[str] = None, subject: str = ""):
        self.mail_processor = GmailProcessor()
        self.recipient: list = recipient or []
        self.subject: str = subject

    @property
    def recipient(self):
        return self._recipient

    @recipient.setter
    def recipient(self, value: list[str]):
        self._recipient = value

    @property
    def subject(self):
        return self._subject

    @subject.setter
    def subject(self, value):
        self._subject = value

    def send(self, notification: Notification) -> bool:
        for recipient in self._recipient:
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


class LineNotificationStrategy(NotificationStrategy):
    """
    A concrete implementation of the `NotificationStrategy` interface that sends notifications via LINE NOTIFY.
    """

    def __init__(self):
        self.mail_strategy = EmailNotificationStrategy()

    def send(self, notification: Notification) -> bool:
        # 實現LINE發送邏輯
        try:
            # TODO: Implement LINE notification sending logic here...
            ...

            return True
        except Exception as e:
            print(f"An error occurred: {e}")
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
