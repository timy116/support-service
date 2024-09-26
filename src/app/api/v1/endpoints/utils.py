from app.models import SpecialHoliday


async def get_cached_holidays(key, redis, year) -> SpecialHoliday:
    return await redis.get_with_auto_set(
        key,
        SpecialHoliday.get_document_by_year,
        year
    )
