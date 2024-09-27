from typing import Annotated, Any

from aioredis import Redis
from fastapi import APIRouter
from fastapi import Depends

from app import schemas
from app.api.v1.endpoints.utils import get_cached_holidays
from app.core.enums import FileTypes
from app.dependencies import daily_reports, special_holidays
from app.dependencies.redis import get_redis
from app.models.daily_reports import DailyReport
from app.utils.email_processors import GmailProcessor, GmailDailyReportSearcher
from app.utils.file_processors import DocumentProcessor

router = APIRouter()


@router.get("")
async def get_daily_reports(
        params: Annotated[daily_reports.CommonParams, Depends(daily_reports.get_common_params)],
        key: Annotated[str, Depends(special_holidays.cache_key)],
        redis: Annotated[Redis, Depends(get_redis)],
        paging: schemas.PaginationParams = Depends(),
        sorting: schemas.SortingParams = Depends()
) -> dict[str, Any]:
    _list = await DailyReport.get_by_params(params, paging, sorting)
    data = await get_cached_holidays(key, redis, params.date.year)

    if params.extract and len(_list) == 0:
        date_of_holidays = [h.date for h in data.holidays]
        d = DocumentProcessor(
            params.date, FileTypes.PDF, product_type=params.product_type, date_of_holidays=date_of_holidays
        )
        p = GmailProcessor(d, GmailDailyReportSearcher)
        daily_report = await DailyReport.get_fulfilled_instance(d, p)

        return {
            "date": daily_report.date,
            "products": daily_report.products
        }
    else:
        return {
            "total": len(_list),
            "daily_reports": _list
        }
