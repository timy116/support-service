from datetime import date
from unittest.mock import AsyncMock

import pytest
from pytest_asyncio import fixture

from app.models.special_holidays import Holiday, HolidayInfo, SpecialHoliday
from app.utils.open_apis import TaiwanCalendarApi
from app.utils.datetime import datetime_formatter


@fixture
def mock_api_data():
    return [
        {
            "date": "2024-01-01",
            "info": {
                "name": "中華民國開國紀念日",
                "holidaycategory": "放假之紀念日及節日"
            }
        }
    ]


@pytest.mark.asyncio
async def test_holiday_date_validator():
    holiday = Holiday(date="2024-01-01", info=HolidayInfo(name="Test", holidaycategory="Test"))
    assert holiday.date == date(2024, 1, 1)

    holiday = Holiday(date=date(2024, 1, 1), info=HolidayInfo(name="Test", holidaycategory="Test"))
    assert holiday.date == date(2024, 1, 1)


@pytest.mark.asyncio
async def test_holiday_model(mock_api_data):
    # Arrange
    d = mock_api_data[0]
    holiday = Holiday(
        date=datetime_formatter(d["date"]),
        info=HolidayInfo(**d["info"])
    )

    # Assert
    assert isinstance(holiday.date, date)
    assert holiday.date == date(2024, 1, 1)
    assert holiday.info.name == d["info"]["name"]
    assert holiday.info.holiday_category == d["info"]["holidaycategory"]


@pytest.mark.asyncio
async def test_special_holiday_create_holidays(mock_api_data):
    # Act
    holidays = await SpecialHoliday.create_holidays(mock_api_data)

    # Assert
    assert len(holidays) == 1
    assert isinstance(holidays[0], Holiday)
    assert holidays[0].date == date(2024, 1, 1)
    assert holidays[0].info.name == mock_api_data[0]["info"]["name"]


@pytest.mark.asyncio
async def test_special_holiday_get_document_by_year(init_db, mocker, mock_api_data):
    # Arrange
    year = 2024
    mock_api = AsyncMock(spec=TaiwanCalendarApi)
    mock_api.get_cleaned_list = AsyncMock(return_value=mock_api_data)
    mocker.patch('app.models.special_holidays.TaiwanCalendarApi', return_value=mock_api)

    # Act
    document = await SpecialHoliday.get_document_by_year(year)

    # Assert
    assert document is not None
    assert document.year == year
    assert len(document.holidays) == 1
    assert document.holidays[0].date == date(2024, 1, 1)
    assert document.holidays[0].info.name == mock_api_data[0]["info"]["name"]

    # Test caching behavior
    second_document = await SpecialHoliday.get_document_by_year(year)
    assert second_document == document
