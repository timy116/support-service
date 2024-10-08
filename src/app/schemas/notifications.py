import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import NotificationCategories, NotificationTypes, LogLevel


class Notification(BaseModel):
    date: datetime.date
    correlation_id: UUID
    category: NotificationCategories
    type: NotificationTypes
    level: LogLevel
    created_at: datetime
