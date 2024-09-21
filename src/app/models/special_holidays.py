from datetime import datetime, date
from typing import Union

from beanie import Document, Indexed
from pydantic import field_validator, Field

from app.utils.datetime import datetime_format
from app.utils.open_apis import TaiwanCalendarApi


class SpecialHoliday(Document):
    date: date
    year: Indexed(int)
    name: str
    is_holiday: bool = Field(..., alias="isholiday")
    holiday_category: str = Field(..., alias="holidaycategory")
    description: Union[str, None] = None

    class Settings:
        name = "special_holidays"
        indexes = ["year", "date"]

    @staticmethod
    def cleaned_value(value: str):
        return value.strip().replace(" ", "").replace("　", "")

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, value: Union[date, str]):
        if isinstance(value, str):
            cleaned_value = cls.cleaned_value(value)
            value = datetime_format(cleaned_value)

        return value

    @field_validator("is_holiday", mode="before")
    @classmethod
    def set_name(cls, value: str):
        if isinstance(value, bool):
            return value

        cleaned_value = cls.cleaned_value(value)

        if cleaned_value == "是":
            return True
        else:
            raise ValueError("is_holiday should be '是'")

    @classmethod
    async def get_documents_by_year(cls, year: int):
        documents = cls.find(cls.year == year)

        if await documents.count() == 0:
            l = await TaiwanCalendarApi(year).cleaned_list
            await cls.insert_many([cls(**d) for d in l])

            documents = cls.find(cls.year == year)

        return documents
