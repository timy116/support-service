from typing import Annotated, Any

from fastapi import APIRouter
from fastapi import Depends

from app.core.enums import RedisCacheKey
from app.dependencies.redis import Redis, get_redis
from app.models import SpecialHoliday

router = APIRouter()


async def cache_key(year: int) -> str:
    return RedisCacheKey.TAIWAN_CALENDAR.value.format(year=year)


@router.get("/holidays/{year}")
async def get_holidays_by_year(
        key: Annotated[str, Depends(cache_key)],
        redis: Annotated[Redis, Depends(get_redis)],
) -> dict[str, Any]:
    data: SpecialHoliday = await redis.get_with_auto_set(
        key,
        SpecialHoliday.get_document_by_year,
        redis.year
    )

    return {
        "total": len(data.holidays),
        "holidays": data.holidays
    }
