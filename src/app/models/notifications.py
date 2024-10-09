import datetime as dt
from datetime import datetime
from uuid import UUID

from beanie import Document

from app.core.enums import NotificationCategories, NotificationTypes, LogLevel
from app.utils.datetime import get_datetime_utc_8, get_date


class Notification(Document):
    date: dt.date = get_date()
    correlation_id: UUID
    category: NotificationCategories
    type: NotificationTypes
    level: LogLevel
    message: str
    created_at: datetime = get_datetime_utc_8()

    class Settings:
        name = "notifications"
        indexes = ["date", "category", "type", "level"]

    @classmethod
    async def create_from_exception(
            cls, correlation_id: str, message: str, t: NotificationTypes = NotificationTypes.LINE
    ):
        return await cls.insert_one(
            cls(
                correlation_id=correlation_id,
                category=NotificationCategories.SYSTEM,
                type=t,
                level=LogLevel.ERROR,
                message=message,
            )
        )

    @classmethod
    async def get_by_params(cls, params, paging, sorting):
        result = cls.find_all()

        if params.date:
            result = result.find(cls.date == params.date)
        if params.category:
            result = result.find(cls.category == params.category)
        if params.type:
            result = result.find(cls.type == params.type)
        if params.level:
            result = result.find(cls.level == params.level)

        return await (
            result
            .skip(paging.skip)
            .limit(paging.limit)
            .sort(sorting.sort)
            .to_list()
        )
