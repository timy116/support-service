from typing import Union

from app.core.enums import RedisCacheKey
from app.utils.datetime import get_date, datetime_format


async def cache_key(year: int = get_date().year, date: Union[str, None] = None) -> str:
    extracted_year = datetime_format(date).year if date else year

    return RedisCacheKey.TAIWAN_CALENDAR.value.format(year=extracted_year)
