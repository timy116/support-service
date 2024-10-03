import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pandas as pd

from app.core.enums import (
    FileTypes,
    ProductType,
    SupplyType,
    Category,
    WeekDay,
    DailyReportType,
)
from app.utils.file_processors import (
    PDFReader,
    DailyReportMetaInfo,
    DailyReportPDFReader,
    FruitDailyReportPDFReader,
    FileReaderFactory,
    DocumentProcessor,
)


##########################################
#### Test `DailyReportMetaInfo` class ####
##########################################
def test_daily_report_meta_info():
    date = datetime(2024, 10, 3).date()
    meta_info = DailyReportMetaInfo(date, ProductType.FRUIT)

    assert meta_info.roc_year == 113
    assert meta_info.date == date
    assert meta_info.product_type == ProductType.FRUIT


def test_daily_reporty_meta_info_get_calculated_report_date(special_holidays):
    # Arrange
    # Case 1: 2024-10-01 is Tuesday
    date = datetime(2024, 10, 1).date()
    weekday = WeekDay(date.isoweekday())
    meta_info = DailyReportMetaInfo(date, ProductType.FRUIT, special_holidays)

    # Act
    calculated_date = meta_info._get_calculated_report_date(weekday)

    # Assert
    assert calculated_date == date

    # Case 2: 2024-09-30 is Monday
    date = datetime(2024, 9, 30).date()
    weekday = WeekDay(date.isoweekday())
    meta_info.date = date

    # Act
    calculated_date = meta_info._get_calculated_report_date(weekday)

    # Assert
    assert calculated_date == date - timedelta(days=2)
    assert WeekDay(calculated_date.isoweekday()) == WeekDay.SATURDAY

    # Case 3: 2024-09-17 is Moon Festival
    date = datetime(2024, 9, 18).date()
    weekday = WeekDay(date.isoweekday())
    meta_info.date = date

    # Act
    calculated_date = meta_info._get_calculated_report_date(weekday)

    # Assert
    assert calculated_date is None


def test_daily_report_meta_info_filename(special_holidays):
    # Arrange
    # Case 1: correct filename with `Fruit`
    date = datetime(2024, 10, 3).date()
    meta_info = DailyReportMetaInfo(date, ProductType.FRUIT, special_holidays)

    # Assert
    assert meta_info.filename == DailyReportType.FRUIT.format(
        roc_year=meta_info.roc_year,
        month=str(date.month).zfill(2),
        day=str(date.day).zfill(2)
    )

    # Case 2: correct filename with `Fish`
    meta_info._filename = None
    date = datetime(2024, 9, 3).date()
    meta_info = DailyReportMetaInfo(date, ProductType.FISH, special_holidays)

    # Assert
    assert meta_info.filename == DailyReportType.FISHERY.format(
        roc_year=meta_info.roc_year,
        month=str(date.month).zfill(2),
        day=str(date.day).zfill(2)
    )

    # Case 3: previous day is holiday
    meta_info._filename = None
    date = datetime(2024, 9, 18).date()
    meta_info.date = date

    # Assert
    assert meta_info.filename == ""

    # Case 4: `ProductType` is not in `DailyReportType`
    meta_info._filename = None
    date = datetime(2024, 9, 3).date()
    meta_info = DailyReportMetaInfo(date, ProductType.FLOWER, special_holidays)

    # Assert
    assert meta_info.filename == ""
