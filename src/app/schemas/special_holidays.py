import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.special_holidays import HolidayInfo


class Holiday:
    date: datetime.date
    info: HolidayInfo


class HolidayCreate(BaseModel):
    date: datetime.date
    name: str
    holiday_category: str
    description: Optional[str] = None
