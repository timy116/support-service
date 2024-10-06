import pickle
from typing import Callable, ParamSpec, Awaitable, Any

from fastapi import Depends
from redis import asyncio as aioredis
from starlette.requests import Request

P = ParamSpec("P")


class Redis:
    def __init__(self, conn: aioredis.Redis):
        self.connection = conn

    async def get_with_auto_set(self, key: str, func: Callable[..., Awaitable[Any]], *args):
        data = await self.connection.get(key)

        if data is None:
            data = await func(*args)
            await self.connection.set(key, pickle.dumps(data))
        else:
            data = pickle.loads(data)

        return data

    async def get(self, key: str):
        return await self.connection.get(key)

    async def delete(self, key: str):
        await self.connection.delete(key)


async def get_connection(request: Request):
    pool: aioredis.Redis = request.app.state.redis_pool

    async with pool.client() as conn:
        yield conn


async def get_redis(conn: aioredis.Redis = Depends(get_connection)) -> Redis:
    return Redis(conn)
