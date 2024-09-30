import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import Category, SupplyType, ProductType
from app.models.daily_reports import Product


class DailyReport(BaseModel):
    date: datetime.date
    category: Category
    supply_type: SupplyType
    product_type: ProductType
    products: list[Product]
    model_config = ConfigDict(from_attributes=True)
