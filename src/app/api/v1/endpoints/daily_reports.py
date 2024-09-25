from datetime import date
from typing import Annotated, Union, Literal

from aioredis import Redis
from fastapi import APIRouter, HTTPException
from fastapi import Depends

from app.core.enums import ProductType, FileTypes
from app.dependencies.redis import get_redis
from app.utils.datetime import datetime_format
from app.utils.email_processors import GmailProcessor, GmailDailyReportSearcher
from app.utils.file_processors import DocumentProcessor

router = APIRouter()


class CommonParams:
    def __init__(self, date: Union[date, None] = None, product_type: Union[str, None] = None, extract: bool = False):
        self.date = date
        self.product_type = ProductType(product_type) if product_type else None
        self.extract = extract


async def get_common_params(
        date: Union[str, None] = None,
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

    return CommonParams(cleaned_date, cleaned_product_type, extract)


@router.get("")
async def get_daily_reports(
        params: Annotated[CommonParams, Depends(get_common_params)],
        redis: Annotated[Redis, Depends(get_redis)],
) -> dict:
    if params.date is None:
        # TODO: return all the daily reports
        ...
    else:
        d = DocumentProcessor(params.date, FileTypes.PDF, params.product_type)
        p = GmailProcessor(d, GmailDailyReportSearcher)
        p.process(d.reader.filename)

    return {"message": "products testing"}
