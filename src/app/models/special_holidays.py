from datetime import date
from typing import Union

from beanie import Document, Indexed
from pydantic import field_validator, Field, BaseModel, ConfigDict

from app.models.utils import clean_value
from app.utils.datetime import datetime_formatter
from app.utils.open_apis import TaiwanCalendarApi


class HolidayInfo(BaseModel):
    name: str
    holiday_category: str = Field(..., alias="holidaycategory")
    description: Union[str, None] = None
    model_config = ConfigDict(populate_by_name=True)


class Holiday(BaseModel):
    date: date
    info: HolidayInfo

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, value: Union[date, str]):
        if isinstance(value, str):
            cleaned_value = clean_value(value)
            value = datetime_formatter(cleaned_value)

        return value


class SpecialHoliday(Document):
    year: Indexed(int)
    holidays: list[Holiday]

    class Settings:
        name = "special_holidays"

    @classmethod
    async def create_holidays(cls, l: list[dict]) -> list[Holiday]:
        return [Holiday(date=d["date"], info=HolidayInfo(**d["info"])) for d in l]

    @classmethod
    async def get_document_by_year(cls, year: int):
        document = cls.find_one(cls.year == year)

        if await document is None:
            l = await TaiwanCalendarApi(year).get_cleaned_list()
            await cls.insert(cls(year=year, holidays=await cls.create_holidays(l)))

            document = cls.find_one(cls.year == year)

        return await document
