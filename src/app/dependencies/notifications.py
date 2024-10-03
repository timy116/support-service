from typing import Union

from app.core.enums import NotificationTypes
from app.utils.notification_helper import NotificationManager, LineNotificationStrategy, EmailNotificationStrategy


async def get_notification_manager(notification_type: Union[NotificationTypes, None] = None) -> NotificationManager:
    if notification_type and notification_type is NotificationTypes.EMAIL:
        return NotificationManager(EmailNotificationStrategy())

    # The default notification type is LINE
    return NotificationManager(LineNotificationStrategy())
