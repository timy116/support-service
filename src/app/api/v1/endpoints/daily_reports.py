from typing import Annotated

from aioredis import Redis
from fastapi import APIRouter, Depends, BackgroundTasks
from starlette.exceptions import HTTPException

from app import schemas
from app.api.v1.endpoints.utils import get_cached_holidays
from app.core.enums import FileTypes, WeekDay
from app.dependencies import daily_reports, special_holidays
from app.dependencies.redis import get_redis
from app.models.daily_reports import DailyReport
from app.schemas import PaginatedDailyReport
from app.utils.datetime import get_date
from app.utils.email_processors import GmailProcessor, GmailDailyReportSearcher
from app.utils.file_processors import DocumentProcessor

router = APIRouter()


@router.get("", response_model=PaginatedDailyReport[schemas.DailyReport])
async def get_daily_reports(
        background_tasks: BackgroundTasks,
        params: Annotated[daily_reports.CommonParams, Depends(daily_reports.get_common_params)],
        key: Annotated[str, Depends(special_holidays.cache_key)],
        redis: Annotated[Redis, Depends(get_redis)],
        paging: schemas.PaginationParams = Depends(),
        sorting: schemas.SortingParams = Depends()
):
    _list = await DailyReport.get_by_params(params, paging, sorting)
    cached_holidays = await get_cached_holidays(key, redis, params.date.year if params.date else get_date().year)
    weekday = None
    response = {
        "page": paging.page,
        "per_page": paging.per_page,
        "total": 0,
        "prev_day_is_holiday": None,
        "weekday": weekday,
        "results": [],
    }

    # the result from the database is only 1 or 0, because the date is unique
    if params.extract and len(_list) <= 1:
        date_of_holidays = [h.date for h in cached_holidays.holidays]
        mail_processor = GmailProcessor(
            DocumentProcessor(
                params.date,
                FileTypes.PDF,
                product_type=params.product_type,
                date_of_holidays=date_of_holidays
            ),
            GmailDailyReportSearcher
        )

        # If there is no daily report in the database, try to get it from the email
        if len(_list) == 0:
            try:
                daily_report = await DailyReport.get_fulfilled_instance(mail_processor)

                # Insert the daily report into the database after the response is returned
                background_tasks.add_task(DailyReport.insert_one, daily_report)
            except:
                raise HTTPException(status_code=500, detail="Internal server error")
        else:
            daily_report = None

        response |= {
            "total": 1 if _list or daily_report else 0,
            "results": [daily_report] if len(_list) == 0 and daily_report else _list,
            "prev_day_is_holiday": mail_processor.document_processor.reader.prev_day_is_holiday,
            "weekday": (WeekDay(params.date.isoweekday())),
        }
    else:
        # If the date is not specified, return the list of daily reports
        response |= {
            "total": len(_list),
            "results": _list,
        }

    return response
