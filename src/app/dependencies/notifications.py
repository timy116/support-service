import datetime
from typing import Union

from app.core.enums import (
    NotificationTypes,
    LogLevel,
)
from app.utils.notification_helper import (
    NotificationManager,
    LineNotificationStrategy,
    EmailNotificationStrategy,
)


class CommonParams:
    def __init__(
            self,
            date: Union[datetime.date, None] = None,
            category: Union[NotificationTypes, None] = None,
            type: Union[NotificationTypes, None] = None,
            level: Union[LogLevel, None] = None
    ):
        self.date = date
        self.category = category
        self.type = type
        self.level = level


async def get_common_params(
        date: Union[datetime.date, None] = None,
        category: Union[NotificationTypes, None] = None,
        type: Union[NotificationTypes, None] = None,
        level: Union[LogLevel, None] = None
) -> CommonParams:
    return CommonParams(date, category, type, level)


async def get_notification_manager(notification_type: Union[NotificationTypes, None] = None) -> NotificationManager:
    if notification_type and notification_type is NotificationTypes.EMAIL:
        return NotificationManager(EmailNotificationStrategy())

    # The default notification type is LINE
    return NotificationManager(LineNotificationStrategy())
