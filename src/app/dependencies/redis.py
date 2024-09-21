import pickle

import aioredis
from fastapi import Depends
from starlette.requests import Request

from app.core.enums import RedisCacheKey
from app.models import SpecialHoliday



class Redis:
    def __init__(self, year: int, conn: aioredis.Redis):
        self.year = year
        self.connection = conn

    async def get(self, key: RedisCacheKey, auto_set=False):
        if auto_set and key == RedisCacheKey.TAIWAN_CALENDAR:
            formatted_key = key.value.format(year=self.year)

        data = await self.connection.get(formatted_key)
        if data is None:

            data = await SpecialHoliday.get_documents_by_year(self.year)
            await self.connection.set(formatted_key, pickle.dumps(data))
        else:
            data = pickle.loads(data)

        return data


async def get_connection(request: Request) -> aioredis.Redis:
    pool = request.app.state.redis_pool

    async with pool.client() as conn:
        yield conn


async def get_redis(year: int, conn: aioredis.Redis = Depends(get_connection)) -> Redis:
    return Redis(year, conn)
