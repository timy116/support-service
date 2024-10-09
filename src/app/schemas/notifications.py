import datetime
from typing import Union
from uuid import UUID

from isapi.samples.redirector import excludes
from pydantic import BaseModel, ConfigDict

from app.core.enums import NotificationCategories, NotificationTypes, LogLevel


class Notification(BaseModel):
    date: datetime.date
    correlation_id: UUID
    category: NotificationCategories
    type: NotificationTypes
    level: LogLevel
    message: str
    created_at: datetime.datetime


class NotificationCreate(BaseModel):
    date: datetime.date
    category: NotificationCategories
    type: NotificationTypes
    level: LogLevel
    message: str
