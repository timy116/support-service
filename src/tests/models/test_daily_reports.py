from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.core.enums import Category, SupplyType, ProductType
from app.models.daily_reports import DailyReport, Product
from app.utils.datetime import get_date, datetime_formatter
from app.utils.email_processors import GmailProcessor


@pytest.fixture
def test_data() -> list[DailyReport]:
    date = get_date().replace(month=9, day=11)

    return [
        DailyReport(
            date=date,
            category=Category.AGRICULTURE,
            supply_type=SupplyType.ORIGIN,
            product_type=ProductType.CROPS,
            products=[
                Product(date=date, product_name="香蕉", average_price=10.0),
                Product(date=date, product_name="芒果", average_price=15.3)
            ]
        ),
        DailyReport(
            date=date,
            category=Category.AGRICULTURE,
            supply_type=SupplyType.WHOLESALE,
            product_type=ProductType.CROPS,
            products=[
                Product(date=date, product_name="香蕉", average_price=10.0),
                Product(date=date, product_name="芒果", average_price=15.3)
            ]
        ),
        DailyReport(
            date=date.replace(day=5),
            category=Category.FISHERY,
            supply_type=SupplyType.ORIGIN,
            product_type=ProductType.SEAFOOD,
            products=[
                Product(date=date, product_name="吳郭魚", average_price=30.5),
            ]
        ),
        DailyReport(
            date=date.replace(day=5),
            category=Category.FISHERY,
            supply_type=SupplyType.WHOLESALE,
            product_type=ProductType.SEAFOOD,
            products=[
                Product(date=date, product_name="白蝦", average_price=100.3)
            ]
        ),
    ]


@pytest.mark.asyncio
async def test_insert_single_instance_into_db(init_db, test_data):
    # Arrange
    date = test_data[0].date

    report = DailyReport(
        date=date.replace(day=10),
        category=Category.AGRICULTURE,
        supply_type=SupplyType.ORIGIN,
        product_type=ProductType.CROPS,
        products=[
            Product(date=date, product_name="香蕉", average_price=10.0),
            Product(date=date, product_name="芒果", average_price=15.3)
        ]
    )

    # Act
    instance = await report.create()

    # Assert
    assert instance is not None


@pytest.mark.asyncio
async def test_read_multi_instances_from_db(init_db, test_data):
    # Arrange
    date = test_data[0].date
    await DailyReport.insert_many(test_data)

    # Act
    # Case 1: query by specific date
    reports = await DailyReport.find_many({"date": date}).to_list()

    # Assert
    assert len(reports) == 2

    # Case 2: query by another date
    reports = await DailyReport.find_many({"date": date.replace(day=5)}).to_list()

    # Assert
    assert len(reports) == 2

    # Case 3: query by category
    reports = await DailyReport.find_many({"supply_type": SupplyType.WHOLESALE}).to_list()

    # Assert
    assert len(reports) == 2
    assert reports[0].product_type == ProductType.CROPS

    # Case 4: query by category and supply type
    reports = await DailyReport.find_many({
        "category": Category.FISHERY,
        "supply_type": SupplyType.WHOLESALE
    }).to_list()

    # Assert
    assert len(reports) == 1

    # Case 5: query by range of dates(<=)
    reports = await DailyReport.find_many(DailyReport.date <= date.replace(day=10)).to_list()

    # Assert
    assert len(reports) == 2

    # Case 6: query by range of dates(>)
    reports = await DailyReport.find_many(
        DailyReport.date > date.replace(day=5),
        DailyReport.date <= get_date()
    ).to_list()

    # Assert
    assert len(reports) == 2


@pytest.mark.asyncio
async def test_update_instance_from_db(init_db, test_data):
    # Arrange
    await DailyReport.insert_many(test_data)

    report = await DailyReport.find_one({
        "category": Category.FISHERY,
        "supply_type": SupplyType.WHOLESALE
    })
    report.supply_type = SupplyType.ORIGIN
    await report.save()

    # Act
    report = await DailyReport.find_one({"_id": report.id})

    # Assert
    assert report is not None
    assert report.updated_at is not None


@pytest.mark.asyncio
async def test_delete_instance_from_db(init_db, test_data):
    # Arrange
    await DailyReport.insert_many(test_data)

    report = await DailyReport.find_one({
        "category": Category.FISHERY,
        "supply_type": SupplyType.WHOLESALE
    })
    await report.delete()

    # Act
    report = await DailyReport.find_one({
        "category": Category.FISHERY,
        "supply_type": SupplyType.WHOLESALE
    })

    # Assert
    assert report is None


@pytest.fixture
def mock_data():
    return [pd.DataFrame({
        '產品別': ['香蕉'],
        '產地': ['平均'],
        '10/2': [11.1],
    }).to_dict(orient="records")]


@pytest.fixture
@patch("app.utils.email_processors.GmailProcessor", new_callable=MagicMock(spec=GmailProcessor))
def mock_mail_processor(mock_mail_processor, mock_data):
    mock_reader = mock_mail_processor.document_processor.reader
    mock_mail_processor.process.return_value = mock_data
    mock_reader.selected_columns = ["產品別", "10/2"]
    mock_reader.PRODUCT_COLUMN = "產品別"
    mock_reader.roc_year = 113
    mock_reader.date = datetime_formatter("20241002")
    mock_reader.category = Category.AGRICULTURE
    mock_reader.supply_type = SupplyType.ORIGIN
    mock_reader.product_type = ProductType.CROPS

    return mock_mail_processor


@pytest.mark.asyncio
async def test_get_fulfilled_instance_returns_correct_instance(mock_mail_processor, init_db):
    # Act
    result = await DailyReport.get_fulfilled_instance(mock_mail_processor)

    # Assert
    assert result is not None
    assert len(result.products) == 1
    assert result.products[0].product_name == "香蕉"
    assert result.products[0].average_price == 11.1


@pytest.mark.asyncio
async def test_get_fulfilled_instance_returns_none(mock_mail_processor):
    # Arrange
    mock_mail_processor.process.return_value = []

    # Act
    result = await DailyReport.get_fulfilled_instance(mock_mail_processor)

    # Assert
    assert result is None
