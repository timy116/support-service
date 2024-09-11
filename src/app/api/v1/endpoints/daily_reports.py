from fastapi import APIRouter


router = APIRouter()


@router.get("")
async def testing():
    return {"message": "products testing"}
