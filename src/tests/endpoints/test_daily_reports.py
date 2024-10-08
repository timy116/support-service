from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.core.enums import (
    DailyReportHttpErrors,
    ProductType,
    WeekDay,
    NotificationCategories,
    NotificationTypes,
    LogLevel
)
from app.dependencies.special_holidays import cache_key
from app.models import DailyReport, Notification
from app.models.special_holidays import SpecialHoliday, HolidayInfo, Holiday
from app.utils.datetime import get_date, datetime_formatter


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
async def test_get_daily_reports_with_no_params(
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
    assert await DailyReport.find_all().count() == 0
    assert mock_get_cached_holidays.called_once_with(key, mock_redis, dt.year)


@pytest.mark.asyncio
async def test_get_daily_reports_with_no_product_type_param(client: TestClient):
    # Act
    response = client.get(
        url="/api/v1/daily-reports",
        params={
            "extract": True,
        }
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["message"] == DailyReportHttpErrors.PRODUCT_TYPE_PARAM_IS_REQUIRED


@pytest.mark.asyncio
async def test_get_daily_reports_with_no_date_param(client: TestClient):
    # Act
    response = client.get(
        url="/api/v1/daily-reports",
        params={
            "product_type": ProductType.CROPS,
            "extract": True,
        }
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["message"] == DailyReportHttpErrors.DATE_PARAM_IS_REQUIRED


@pytest.mark.asyncio
async def test_get_daily_reports_with_invalid_date_param(client: TestClient):
    # Act
    response = client.get(
        url="/api/v1/daily-reports",
        params={
            "date": "invalid date",
        }
    )

    # Assert
    assert response.status_code == 400


@pytest.mark.asyncio
@patch("app.api.v1.endpoints.daily_reports.DailyReport.get_fulfilled_instance", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.daily_reports.DailyReport.get_by_params", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.daily_reports.get_cached_holidays", new_callable=AsyncMock)
async def test_get_daily_reports_with_extract_param(
        mock_get_cached_holidays,
        mock_get_by_params,
        mock_get_fulfilled_instance,
        init_db,
        mock_cached_holidays,
        mock_daily_reports: list[DailyReport],
        client: TestClient
):
    # Arrange
    dt = "20241002"
    mock_get_cached_holidays.return_value = mock_cached_holidays
    mock_get_by_params.return_value = []
    daily_report = mock_daily_reports[0]
    mock_get_fulfilled_instance.return_value = daily_report

    # Act
    response = client.get(
        url="/api/v1/daily-reports",
        params={
            "date": dt,
            "product_type": ProductType.CROPS,
            "extract": True,
        }
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["page"] == 1
    assert response.json()["per_page"] == 10
    assert response.json()["total"] == 1
    assert response.json()["prev_day_is_holiday"] == False
    assert response.json()["weekday"] is WeekDay(datetime_formatter(dt).isoweekday()).value
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["date"] == daily_report.date.strftime("%Y-%m-%d")
    assert await DailyReport.find_all().count() == 1
    assert await DailyReport.find_one(DailyReport.date == daily_report.date) == daily_report


@pytest.mark.asyncio
@patch("app.api.v1.endpoints.daily_reports.correlation_id", new_callable=MagicMock)
@patch("app.api.v1.endpoints.daily_reports.NotificationManager.send_notification", new_callable=MagicMock)
@patch("app.api.v1.endpoints.daily_reports.Notification.create_from_exception", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.daily_reports.DailyReport.get_fulfilled_instance", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.daily_reports.DailyReport.get_by_params", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.daily_reports.get_cached_holidays", new_callable=AsyncMock)
async def test_get_daily_reports_with_extract_param_failed(
        mock_get_cached_holidays,
        mock_get_by_params,
        mock_get_fulfilled_instance,
        mock_create_from_exception,
        mock_send_notification,
        mock_correlation_id,
        init_db,
        mock_cached_holidays,
        client: TestClient
):
    # Arrange
    dt = "20241002"
    mock_correlation_id.get.return_value = uuid4().hex
    _id = mock_correlation_id.get()
    error_msg = DailyReportHttpErrors.FAILED
    notification = await Notification.insert_one(
        Notification(
            correlation_id=_id,
            category=NotificationCategories.SERVICE,
            type=NotificationTypes.LINE,
            level=LogLevel.ERROR,
            message=str(error_msg)
        )
    )
    mock_get_cached_holidays.return_value = mock_cached_holidays
    mock_create_from_exception.return_value = notification
    mock_get_by_params.return_value = []
    mock_get_fulfilled_instance.side_effect = Exception("Failed to get daily report")

    # Act
    response = client.get(
        url="/api/v1/daily-reports",
        params={
            "date": dt,
            "product_type": ProductType.CROPS,
            "extract": True,
        }
    )

    # Assert
    assert response.status_code == 500
    assert response.json()["message"] == DailyReportHttpErrors.INTERNAL_SERVER_ERROR.value
    mock_create_from_exception.assert_called_once_with(_id, str(error_msg))
    mock_send_notification.assert_called_once_with(notification)


@pytest.mark.asyncio
@patch("app.api.v1.endpoints.daily_reports.DailyReport.get_fulfilled_instance", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.daily_reports.DailyReport.get_by_params", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.daily_reports.get_cached_holidays", new_callable=AsyncMock)
async def test_get_daily_reports_with_extract_param_and_single_daily_report_instance(
        mock_get_cached_holidays,
        mock_get_by_params,
        mock_get_fulfilled_instance,
        init_db,
        mock_cached_holidays,
        mock_daily_reports: list[DailyReport],
        client: TestClient
):
    # Arrange
    dt = "20241002"
    mock_get_cached_holidays.return_value = mock_cached_holidays
    mock_get_by_params.return_value = [mock_daily_reports[0]]
    daily_report = mock_daily_reports[0]

    # Act
    response = client.get(
        url="/api/v1/daily-reports",
        params={
            "date": dt,
            "product_type": ProductType.CROPS,
            "extract": True,
        }
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["page"] == 1
    assert response.json()["per_page"] == 10
    assert response.json()["total"] == 1
    assert response.json()["prev_day_is_holiday"] == False
    assert response.json()["weekday"] is WeekDay(datetime_formatter(dt).isoweekday()).value
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["date"] == daily_report.date.strftime("%Y-%m-%d")
    assert await DailyReport.find_all().count() == 0
    mock_get_fulfilled_instance.assert_not_called()
