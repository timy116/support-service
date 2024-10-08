import datetime
from typing import Union, Literal

from fastapi import HTTPException

from app.core.enums import Category, ProductType, SupplyType, DailyReportHttpErrors
from app.utils.datetime import datetime_formatter


class CommonParams:
    def __init__(
            self, date: Union[datetime.date, None] = None,
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
        product_type: Union[Literal[ProductType.CROPS, ProductType.SEAFOOD], None] = None,
        extract: bool = False
) -> CommonParams:
    try:
        cleaned_date = datetime_formatter(date) if date else None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if extract:
        if product_type is None:
            raise HTTPException(status_code=400, detail=DailyReportHttpErrors.PRODUCT_TYPE_PARAM_IS_REQUIRED)
        if date is None:
            raise HTTPException(status_code=400, detail=DailyReportHttpErrors.DATE_PARAM_IS_REQUIRED)

    return CommonParams(cleaned_date, supply_type, category, product_type, extract)
