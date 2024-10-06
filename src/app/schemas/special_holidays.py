import datetime

from pydantic import BaseModel

from app.models.special_holidays import HolidayInfo


class Holiday(BaseModel):
    date: datetime.date
    info: HolidayInfo


class HolidayCreate(Holiday):
    pass
