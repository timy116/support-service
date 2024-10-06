from typing import Annotated, Any

from fastapi import APIRouter
from fastapi import Depends
from starlette import status
from starlette.exceptions import HTTPException

from app import schemas
from app.api.v1.endpoints.utils import get_cached_holidays
from app.dependencies.redis import Redis, get_redis
from app.dependencies.special_holidays import cache_key
from app.models.special_holidays import Holiday, SpecialHoliday

router = APIRouter()


@router.get("/holidays/{year}")
async def get_holidays_by_year(
        year: int,
        key: Annotated[str, Depends(cache_key)],
        redis: Annotated[Redis, Depends(get_redis)],
) -> dict[str, Any]:
    data = await get_cached_holidays(key, redis, year)

    return {
        "total": len(data.holidays),
        "holidays": data.holidays
    }


@router.post("/holidays", response_model=schemas.Holiday, status_code=status.HTTP_201_CREATED)
async def create_holiday(holiday_in: schemas.HolidayCreate, redis: Annotated[Redis, Depends(get_redis)]) -> Holiday:
    data = holiday_in.model_dump()
    holiday = Holiday(**data)
    special_holiday = await SpecialHoliday.find_one(SpecialHoliday.year == holiday.date.year)

    if special_holiday is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The year does not exist.")
    if holiday in special_holiday.holidays:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The holiday already exists.")

    special_holiday.holidays.append(holiday)
    await special_holiday.save()

    # delete the cache for the year
    await redis.delete(await cache_key(holiday.date.year))

    return holiday
