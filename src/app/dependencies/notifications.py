import datetime
from typing import Union, Any

from fastapi import HTTPException

from app import schemas
from app.core.enums import (
    NotificationTypes,
    LogLevel, NotificationCategories,
)
from app.middlewares.correlation import correlation_id
from app.models import Notification
from app.utils.datetime import datetime_formatter
from app.utils.notification_helper import (
    NotificationManager,
    LineNotificationStrategy,
    EmailNotificationStrategy,
)


class CommonParams:
    def __init__(
            self,
            date: Union[datetime.date, None] = None,
            category: Union[NotificationCategories, None] = None,
            type: Union[NotificationTypes, None] = None,
            level: Union[LogLevel, None] = None
    ):
        self.date = date
        self.category = category
        self.type = type
        self.level = level


async def get_common_params(
        date: Union[str, None] = None,
        category: Union[NotificationCategories, None] = None,
        type: Union[NotificationTypes, None] = None,
        level: Union[LogLevel, None] = None
) -> CommonParams:
    try:
        cleaned_date = datetime_formatter(date) if date else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return CommonParams(cleaned_date, category, type, level)


async def get_notification_manager(notification_type: Union[NotificationTypes, None] = None) -> NotificationManager:
    if notification_type and notification_type is NotificationTypes.EMAIL:
        return NotificationManager(EmailNotificationStrategy())

    # The default notification type is LINE
    return NotificationManager(LineNotificationStrategy())


async def get_notification_in(notification_in: schemas.NotificationCreate) -> Notification:
    dump = notification_in.model_dump()
    dump["correlation_id"] = correlation_id.get()

    return Notification(**dump)
