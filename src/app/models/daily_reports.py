from datetime import datetime, date
from typing import Optional

from beanie import Document, Indexed, WriteRules
from beanie.odm.documents import DocType
from pydantic import BaseModel, ConfigDict
from pymongo.client_session import ClientSession

from app.core.enums import Category, SupplyType, ProductType
from app.dependencies.daily_reports import CommonParams
from app.schemas import PaginationParams, SortingParams
from app.utils.datetime import get_datetime_utc_8, datetime_formatter
from app.utils.email_processors import GmailProcessor
from app.utils.file_processors import DocumentProcessor, FruitDailyReportPDFReader


class Product(BaseModel):
    date: date
    product_name: str
    average_price: float


class DailyReport(Document):
    date: Indexed(date)
    category: Category
    supply_type: SupplyType
    product_type: ProductType
    products: list[Product]
    created_at: datetime = get_datetime_utc_8()
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2024-09-11",
                "category": "農產品",
                "supply_type": "產地",
                "product_type": "水果",
                "products": [
                    {
                        "date": "2024-09-10",
                        "product_name": "香蕉",
                        "average_price": 10.0
                    },
                    {
                        "date": "2024-09-10",
                        "product_name": "芒果",
                        "average_price": 15.3
                    }
                ]
            }
        }
    )

    class Settings:
        name = "daily_reports"
        indexes = ["date", "category", "supply_type", "product_type"]

    async def save(self: DocType, session: Optional[ClientSession] = None,
                   link_rule: WriteRules = WriteRules.DO_NOTHING, ignore_revision: bool = False, **kwargs) -> DocType:
        self.updated_at = get_datetime_utc_8()
        return await super().save(session, link_rule, ignore_revision, **kwargs)

    @classmethod
    async def get_by_params(cls, params: CommonParams, paging: PaginationParams, sorting: SortingParams):
        return await (
            cls.find(
                cls.date == params.date,
                cls.category == params.category,
                cls.supply_type == params.supply_type,
                cls.product_type == params.product_type
            )
            .skip(paging.skip)
            .limit(paging.limit)
            .sort(sorting.sort)
            .to_list()
        )

    @classmethod
    async def get_fulfilled_instance(cls, doc_processor: DocumentProcessor, mail_processor: GmailProcessor):
        if not (result := mail_processor.process(doc_processor.reader.filename)):
            return

        reader: FruitDailyReportPDFReader = doc_processor.reader
        cols = doc_processor.reader.selected_columns
        products = []

        for d in result[0]:
            for col in cols:
                if col == reader.PRODUCT_COLUMN:
                    continue

                product_date = datetime_formatter(f"{reader.roc_year}/{col}")
                if d[col] != 0:
                    product_name = d[reader.PRODUCT_COLUMN]

                    products.append(
                        Product(date=product_date, product_name=product_name, average_price=d[col])
                    )

        return cls(
            date=reader.date,
            category=reader.category,
            supply_type=reader.supply_type,
            product_type=reader.product_type,
            products=products
        )
