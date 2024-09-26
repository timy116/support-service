from datetime import date
from typing import Union, Literal

from fastapi import HTTPException

from app.core.enums import Category, ProductType, SupplyType
from app.utils.datetime import datetime_format


class CommonParams:
    def __init__(
            self, date: Union[date, None] = None,
            supply_type: Union[SupplyType, None] = None,
            category: Union[Category, None] = None,
            product_type: Union[ProductType, None] = None,
            extract: bool = False
    ):
        self.date = date
        self.supply_type = supply_type
        self.category = category
        self.product_type = product_type
        self.extract = extract


async def get_common_params(
        date: Union[str, None] = None,
        supply_type: Union[SupplyType, None] = None,
        category: Union[Category, None] = None,
        product_type: Union[Literal[ProductType.FRUIT, ProductType.FISH], None] = None,
        extract: bool = False
) -> CommonParams:
    try:
        cleaned_date = datetime_format(date) if date else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        cleaned_product_type = ProductType(product_type) if product_type else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if extract and cleaned_product_type is None:
        raise HTTPException(status_code=400, detail='product_type is required when extract is set')

    return CommonParams(cleaned_date, supply_type, category, cleaned_product_type, extract)
