from fastapi import APIRouter
from fastapi import Depends
from app.api.v1.deps import get_redis
from aioredis import Redis

router = APIRouter()


@router.get("")
async def testing(redis: Redis = Depends(get_redis)) -> dict:
    print(f'Connection: {redis}')

    return {"message": "products testing"}
