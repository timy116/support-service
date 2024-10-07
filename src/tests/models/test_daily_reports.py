import pytest

from app.core.enums import Category, SupplyType, ProductType
from app.models.daily_reports import DailyReport, Product
from app.utils.datetime import get_date


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
