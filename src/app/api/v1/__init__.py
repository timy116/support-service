from fastapi import APIRouter

from app.api.v1.endpoints import daily_reports, special_holidays, notifications
from app.core.config import settings

router = APIRouter(prefix=f"/{settings.API_V1_STR}")
router.include_router(daily_reports.router, prefix="/daily-reports", tags=["Daily Reports"])
router.include_router(special_holidays.router, prefix="/special-holidays", tags=["Special Holidays"])
router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
