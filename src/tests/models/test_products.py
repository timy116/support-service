from unittest import IsolatedAsyncioTestCase

import pytest
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from src.app.models.daily_reports import DailyReport, Product
from src.app.models.utils import get_datetime_utc_8


class TestDailyReport(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        client = AsyncMongoMockClient('mongodb://user:pass@host:27017/', connectTimeoutMS=250)
        await init_beanie(
            database=client.beanie_test,
            document_models=[DailyReport],
        )
        await self.create_data()

    async def create_data(self):
        self.date = get_datetime_utc_8()

        reports = [
            DailyReport(
                date=self.date,
                category="水果",
                source="產地",
                products=[
                    Product(product_name="香蕉", average_price=10.0),
                    Product(product_name="芒果", average_price=15.3)
                ]
            ),
            DailyReport(
                date=self.date,
                category="水果",
                source="批發",
                products=[
                    Product(product_name="香蕉", average_price=10.0),
                    Product(product_name="芒果", average_price=15.3)
                ]
            ),
            DailyReport(
                date=self.date.replace(day=5),
                category="漁產",
                source="產地",
                products=[
                    Product(product_name="吳郭魚", average_price=30.5),
                    Product(product_name="白蝦", average_price=100.3)
                ]
            ),
            DailyReport(
                date=self.date.replace(day=5),
                category="漁產",
                source="批發",
                products=[
                    Product(product_name="吳郭魚", average_price=30.5),
                    Product(product_name="白蝦", average_price=100.3)
                ]
            ),
        ]

        await DailyReport.insert_many(reports)

    @pytest.mark.asyncio
    async def test_insert_single_instance_into_db(self):
        date = get_datetime_utc_8()

        report = DailyReport(
            date=date.replace(day=10),
            category="水果",
            source="產地",
            products=[
                Product(product_name="香蕉", average_price=10.0),
                Product(product_name="芒果", average_price=15.3)
            ]
        )
        await report.create()

    @pytest.mark.asyncio
    async def test_read_multi_instances_from_db(self):
        reports = await DailyReport.find_many({"date": self.date}).to_list()

        assert len(reports) == 2

        reports = await DailyReport.find_many({"date": self.date.replace(day=5)}).to_list()

        assert len(reports) == 2

        reports = await DailyReport.find_many({"source": "批發"}).to_list()

        assert len(reports) == 2
        assert reports[0].category == "水果"

        reports = await DailyReport.find_many({"category": "漁產", "source": "批發"}).to_list()

        assert len(reports) == 1

    @pytest.mark.asyncio
    async def test_update_instance_from_db(self):
        report = await DailyReport.find_one({"category": "漁產", "source": "批發"})
        report.source = "產地"
        await report.save()

        report = await DailyReport.find_one({"category": "漁產", "source": "產地"})
        assert report is not None

    @pytest.mark.asyncio
    async def test_delete_instance_from_db(self):
        report = await DailyReport.find_one({"category": "漁產", "source": "批發"})
        await report.delete()

        report = await DailyReport.find_one({"category": "漁產", "source": "批發"})
        assert report is None
