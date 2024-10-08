from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from app.core.enums import (
    FileTypes,
    ProductType,
    SupplyType,
    Category,
    WeekDay,
    DailyReportType,
)
from app.utils.file_processors import (
    DailyReportMetaInfo,
    DailyReportPDFReader,
    FruitDailyReportPDFReader,
    FileReaderFactory,
    DocumentProcessor,
    FishDailyReportPDFReader,
)


class TestFileReaderFactory:
    def test_file_reader_factory(self):
        date = datetime(2024, 10, 3).date()
        reader = FileReaderFactory.get_reader(date, FileTypes.PDF, ProductType.CROPS)

        assert isinstance(reader, FruitDailyReportPDFReader)

    def test_daily_report_pdf_reader_factory(self):
        # Arrange
        # Case 1: `ProductType` is `FRUIT`
        date = datetime(2024, 10, 3).date()
        reader = DailyReportPDFReader.get_daily_report_reader(date, ProductType.CROPS)

        # Assert
        assert isinstance(reader, FruitDailyReportPDFReader)

        # Case 2: `ProductType` is `FISH`
        reader = DailyReportPDFReader.get_daily_report_reader(date, ProductType.SEAFOOD)

        # Assert
        assert isinstance(reader, FishDailyReportPDFReader)

        # Case 3: `ProductType` is not in `DailyReportType`
        reader = DailyReportPDFReader.get_daily_report_reader(date, ProductType.VEGETABLE)

        # Assert
        assert isinstance(reader, DailyReportPDFReader)


class TestDocumentProcessor:
    def test_document_processor(self):
        # Arrange
        # Case 1: `ProductType` is `FRUIT`
        date = datetime(2024, 10, 3).date()
        processor = DocumentProcessor(date, FileTypes.PDF, ProductType.CROPS)

        # Assert
        assert isinstance(processor.reader, FruitDailyReportPDFReader)

        # Case 2: `ProductType` is `FISH`
        processor = DocumentProcessor(date, FileTypes.PDF, ProductType.SEAFOOD)

        # Assert
        assert isinstance(processor.reader, FishDailyReportPDFReader)


class TestDailyReportMetaInfo:
    def test_daily_report_meta_info(self):
        date = datetime(2024, 10, 3).date()
        meta_info = DailyReportMetaInfo(date, ProductType.CROPS)

        assert meta_info.roc_year == 113
        assert meta_info.date == date
        assert meta_info.product_type == ProductType.CROPS

    def test_daily_reporty_meta_info_get_calculated_report_date(self, special_holidays):
        # Arrange
        # Case 1: 2024-10-01 is Tuesday
        date = datetime(2024, 10, 1).date()
        weekday = WeekDay(date.isoweekday())
        meta_info = DailyReportMetaInfo(date, ProductType.CROPS, special_holidays)

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

    def test_daily_report_meta_info_filename(self, special_holidays):
        # Arrange
        # Case 1: correct filename with `Fruit`
        date = datetime(2024, 10, 3).date()
        meta_info = DailyReportMetaInfo(date, ProductType.CROPS, special_holidays)

        # Assert
        assert meta_info.filename == DailyReportType.CROPS.format(
            roc_year=meta_info.roc_year,
            month=str(date.month).zfill(2),
            day=str(date.day).zfill(2)
        )

        # Case 2: correct filename with `Fish`
        meta_info._filename = None
        date = datetime(2024, 9, 3).date()
        meta_info = DailyReportMetaInfo(date, ProductType.SEAFOOD, special_holidays)

        # Assert
        assert meta_info.filename == DailyReportType.SEAFOOD.format(
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


class TestFruitDailyReportPDFReader:
    def test_fruit_daily_report_pdf_reader(self, special_holidays):
        date = datetime(2024, 10, 3).date()
        reader = FruitDailyReportPDFReader(date, ProductType.CROPS, special_holidays)

        assert reader.supply_type == SupplyType.ORIGIN
        assert reader.category == Category.AGRICULTURE

    @pytest.mark.parametrize("date,expected", [
        (datetime(2024, 9, 18), True),  # Moon Festival
        (datetime(2024, 9, 30), True),  # Monday
        (datetime(2024, 10, 3), False),  # Thursday
        (datetime(2024, 10, 5), True),  # Saturday
        (datetime(2024, 10, 6), True),  # Sunday
    ])
    def test_fruit_daily_report_pdf_reader_prev_day_is_holiday(self, date, expected, special_holidays):
        reader = FruitDailyReportPDFReader(date.date(), ProductType.CROPS, special_holidays)
        assert reader.prev_day_is_holiday == expected

    @pytest.mark.parametrize("date,expected_columns", [
        (datetime(2024, 10, 14), ['產品別', '10/10', '10/11']),
        (datetime(2024, 10, 7), ['產品別', '10/4']),
        (datetime(2024, 10, 3), ['產品別', '10/2']),
        (datetime(2024, 10, 1), ['產品別', '9/28', '9/29', '9/30']),
        (datetime(2024, 9, 19), ['產品別', '9/17', '9/18']),
    ])
    def test_fruit_daily_report_pdf_reader_selected_columns(self, date, expected_columns, special_holidays):
        reader = FruitDailyReportPDFReader(date.date(), ProductType.CROPS, special_holidays)

        assert reader.selected_columns == expected_columns

    @patch('fitz.open')
    def test_fruit_daily_report_pdf_reader_extract_data(self, mock_fitz, special_holidays):
        # Arrange
        # Case 1: normal case
        date = datetime(2024, 10, 3).date()
        reader = FruitDailyReportPDFReader(date, ProductType.CROPS, special_holidays)
        reader._get_tables_data = Mock(return_value=pd.DataFrame({
            '產品別': ['香蕉\n產地價格監控'],
            '產地': ['平均'],
            '10/2': ['11.1\n'],
        }))
        mock_doc = Mock()
        mock_fitz.return_value = mock_doc

        # Act
        result = reader._extract_data_from_file("test.pdf")

        # Assert
        assert len(result) == 1
        assert result[0]['產品別'] == '香蕉'
        assert result[0]['10/2'] == 11.1

        # Case 2: daily report on Tuesday
        date = datetime(2024, 10, 1).date()
        reader = FruitDailyReportPDFReader(date, ProductType.CROPS, special_holidays)
        reader._get_tables_data = Mock(return_value=pd.DataFrame({
            '產品別': ['香蕉\n產地價格監控', '檸檬\n產地價格監控'],
            '產地': ['平均', '平均'],
            '9/28': ['11.1\n', '22.2\n'],
            '9/29': ['22.2\n', '33.3\n'],
            '9/30': ['－', '44.4\n'],
        }))

        # Act
        result = reader._extract_data_from_file("test.pdf")

        # Assert
        assert len(result) == 2
        assert result[0]['產品別'] == '香蕉'
        assert result[0]['9/28'] == 11.1
        assert result[0]['9/29'] == 22.2
        assert result[0]['9/30'] == 0
        assert result[1]['產品別'] == '檸檬'
        assert result[1]['9/28'] == 22.2
        assert result[1]['9/29'] == 33.3
        assert result[1]['9/30'] == 44.4

        # Case 3: daily report on Moon Festival
        date = datetime(2024, 9, 19).date()
        reader = FruitDailyReportPDFReader(date, ProductType.CROPS, special_holidays)
        reader._get_tables_data = Mock(return_value=pd.DataFrame({
            '產品別': ['香蕉\n產地價格監控', '檸檬\n產地價格監控'],
            '產地': ['平均', '平均'],
            '9/17': ['11.1\n', '22.2\n'],
            '9/18': ['22.2\n', '33.3\n'],
        }))

        # Act
        result = reader._extract_data_from_file("test.pdf")

        # Assert
        assert len(result) == 2
        assert result[0]['產品別'] == '香蕉'
        assert result[0]['9/17'] == 11.1
        assert result[0]['9/18'] == 22.2
        assert result[1]['產品別'] == '檸檬'
        assert result[1]['9/17'] == 22.2
        assert result[1]['9/18'] == 33.3

        # Case 4: daily report on Monday
        date = datetime(2024, 10, 7).date()
        reader = FruitDailyReportPDFReader(date, ProductType.CROPS, special_holidays)
        reader._get_tables_data = Mock(return_value=pd.DataFrame({
            '產品別': ['香蕉\n產地價格監控'],
            '產地': ['平均'],
            '10/4': ['11.1\n'],
        }))

        # Act
        result = reader._extract_data_from_file("test.pdf")

        # Assert
        assert len(result) == 1
        assert result[0]['產品別'] == '香蕉'
        assert result[0]['10/4'] == 11.1
