from typing import Annotated, Any

from fastapi import APIRouter
from fastapi import Depends

from app.api.v1.endpoints.utils import get_cached_holidays
from app.dependencies.redis import Redis, get_redis
from app.dependencies.special_holidays import cache_key

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
