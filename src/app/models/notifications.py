from datetime import datetime, date
from uuid import UUID

from beanie import Document, Indexed

from app.core.enums import NotificationCategories, NotificationTypes, LogLevel
from app.utils.datetime import get_datetime_utc_8


class Notification(Document):
    date: Indexed(date)
    correlation_id: UUID
    category: NotificationCategories
    type: NotificationTypes
    level: LogLevel
    message: str
    created_at: datetime = get_datetime_utc_8()

    class Settings:
        name = "notifications"
        indexes = ["date", "category", "type", "level"]
