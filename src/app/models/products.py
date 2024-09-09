from datetime import datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import BaseModel


class Product(BaseModel):
    product_name: str
    average_price: float


class DailyReport(Document):
    date: Indexed(datetime)
    category: Indexed(str)
    source: Indexed(str)
    products: list[Product]
    updated_at: Optional[datetime]

    class Settings:
        collection = "daily_reports"
        indexes = ["date", "category", "source"]
