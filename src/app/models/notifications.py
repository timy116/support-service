from datetime import datetime, date

from beanie import Document, Indexed

from app.core.enums import NotificationCategories, NotificationTypes
from app.utils.datetime import get_datetime_utc_8


class Notification(Document):
    date: Indexed(date)
    category: NotificationCategories
    type: NotificationTypes
    message: str
    created_at: datetime = get_datetime_utc_8()

    class Settings:
        name = "notifications"
        indexes = ["date", "category", "type"]
