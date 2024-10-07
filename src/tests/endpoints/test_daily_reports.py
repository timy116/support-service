from unittest.mock import patch, AsyncMock

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.dependencies.special_holidays import cache_key
from app.models import DailyReport
from app.models.special_holidays import SpecialHoliday, HolidayInfo, Holiday
from app.utils.datetime import get_date


@pytest.fixture
def mock_cached_holidays():
    return SpecialHoliday(
        year=2024,
        holidays=[
            Holiday(
                date="20240917",
                info=HolidayInfo(
                    name="中秋節",
                    holiday_category="放假之紀念日及節日",
                    description="全國各機關學校放假一日。",
                ),
            ),
        ]
    )


@pytest.mark.asyncio
@patch("app.api.v1.endpoints.daily_reports.DailyReport.get_by_params", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.daily_reports.get_cached_holidays", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.daily_reports.BackgroundTasks")
async def test_get_daily_reports_with_no_params(
        mock_background_tasks,
        mock_get_cached_holidays,
        mock_get_by_params,
        init_db,
        mock_cached_holidays,
        mock_daily_reports: list[DailyReport],
        client: TestClient,
        test_app: tuple[FastAPI, AsyncMock]
):
    # Arrange
    _, mock_redis = test_app
    dt = get_date()
    key = await cache_key(dt.year)
    mock_get_cached_holidays.return_value = mock_cached_holidays
    mock_get_by_params.return_value = mock_daily_reports

    # Act
    response = client.get("/api/v1/daily-reports")

    # Assert
    assert response.status_code == 200
    assert response.json()["page"] == 1
    assert response.json()["per_page"] == 10
    assert response.json()["total"] == 4
    assert response.json()["prev_day_is_holiday"] is None
    assert response.json()["weekday"] is None
    assert len(response.json()["results"]) == 4
    assert mock_background_tasks.return_value.add_task.never_called()
    assert mock_get_cached_holidays.called_once_with(key, mock_redis, dt.year)

# TODO: Add more tests
