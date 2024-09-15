import aioredis
from fastapi import Request


async def get_redis(request: Request) -> aioredis.Redis:
    pool = request.app.state.redis_pool

    async with pool.client() as conn:
        yield conn
