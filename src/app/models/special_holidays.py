from datetime import datetime, date
from typing import Union

from beanie import Document, Indexed
from pydantic import field_validator, Field


class SpecialHoliday(Document):
    date: date
    year: Indexed(int)
    name: str
    is_holiday: bool = Field(..., alias="isholiday")
    holiday_category: str = Field(..., alias="holidaycategory")
    description: Union[str, None] = None

    class Settings:
        name = "special_holidays"

    @staticmethod
    def cleaned_value(value: str):
        return value.strip().replace(" ", "").replace("　", "")

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, value: Union[date, str]):
        if isinstance(value, str):
            cleaned_value = cls.cleaned_value(value)

            if len(cleaned_value) == 8:
                value = datetime.strptime(value, "%Y%m%d").date()
            elif cleaned_value.find('-') == 3:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            elif cleaned_value.find('/') == 3:
                value = datetime.strptime(value, "%Y/%m/%d").date()
            elif cleaned_value.find('.') == 3:
                value = datetime.strptime(value, "%Y.%m.%d").date()
            else:
                raise ValueError("Invalid date format")

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
