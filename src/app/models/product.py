from typing import Optional

from beanie import Document, Indexed
from pydantic import BaseModel


class Category(BaseModel):
    name: str
    description: str


class Product(Document):
    name: str
    description: Optional[str] = None
    price: Indexed(float)
    category: Category
