from fastapi import APIRouter
from app.api.v1.endpoints.products.fruits.origin import products
from app.core.config import settings


router = APIRouter(prefix=f"/{settings.API_V1_STR}")
router.include_router(products.router, prefix="/products/fruits/origin", tags=["Fruits Origin Products"])
