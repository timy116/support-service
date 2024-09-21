from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends

from app.core.enums import RedisCacheKey
from app.dependencies.redis import Redis, get_redis
from app.models import SpecialHoliday

router = APIRouter()


async def cache_key() -> str:
    return RedisCacheKey.TAIWAN_CALENDAR


@router.get("/holidays/{year}")
async def get_holidays_by_year(
        key: Annotated[RedisCacheKey, Depends(cache_key)], redis: Annotated[Redis, Depends(get_redis)]
) -> dict:
    data = await redis.get(key, auto_set=True)

    if data is None:
        return {"message": "No data"}
    else:
        return {
            "result": await data.to_list()
        }
