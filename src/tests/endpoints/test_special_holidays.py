import pytest
from fastapi.testclient import TestClient

from app.dependencies.special_holidays import cache_key
from app.models.special_holidays import SpecialHoliday, Holiday, HolidayInfo


@pytest.fixture
def get_test_data() -> SpecialHoliday:
    return SpecialHoliday(
        year=2024,
        holidays=[
            Holiday(
                date="2024-01-01",
                info=HolidayInfo(
                    name="放假之紀念日及節日",
                    holiday_category="國定假日",
                    description="全國各機關學校放假一日。"
                )
            )
        ]
    )


@pytest.mark.asyncio
async def test_create_holiday(test_app, init_db, client: TestClient, get_test_data):
    # Arrange
    _, mock_redis = test_app
    key = await cache_key(get_test_data.year)
    json_data = {
        "date": "2024-10-03",
        "info": {
            "name": "113年10月3日天然災害停止辦公及上課情形(山陀兒颱風)",
            "holidaycategory": "颱風假",
            "description": None,
        }
    }
    await SpecialHoliday.create(get_test_data)

    # Act
    response = client.post(
        "/api/v1/special-holidays/holidays",
        json=json_data
    )

    # Assert
    assert response.status_code == 201
    assert response.json() == json_data
    mock_redis.delete.assert_called_once_with(key)
