from fastapi import APIRouter
from app.api.v1.endpoints import daily_reports
from app.core.config import settings


router = APIRouter(prefix=f"/{settings.API_V1_STR}")
router.include_router(daily_reports.router, prefix="/daily_reports", tags=["Daily Reports"])
