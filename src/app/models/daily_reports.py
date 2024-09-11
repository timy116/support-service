from datetime import datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import BaseModel, ConfigDict


class Product(BaseModel):
    product_name: str
    average_price: float


class DailyReport(Document):
    date: Indexed(datetime)
    category: Indexed(str)
    source: Indexed(str)
    products: list[Product]
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2024-09-11 09:16:52.864443+08:00",
                "category": "水果",
                "source": "產地",
                "products": [
                    {
                        "product_name": "香蕉",
                        "average_price": 10.0
                    },
                    {
                        "product_name": "芒果",
                        "average_price": 15.3
                    }
                ]
            }
        }
    )

    class Settings:
        name = "daily_reports"
        indexes = ["date", "category", "source"]
