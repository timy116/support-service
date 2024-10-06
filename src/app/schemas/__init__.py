from typing import Union

from pydantic import ConfigDict

from .daily_reports import DailyReport
from .pagination import Paginated, PaginationParams
from .sorting import SortingParams
from .special_holidays import HolidayCreate, Holiday
from ..core.enums import WeekDay


class PaginatedDailyReport(Paginated):
    weekday: Union[WeekDay, None]
    prev_day_is_holiday: Union[bool, None]
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "page": 1,
                "per_page": 10,
                "total": 1,
                "results": [
                    {
                        "date": "2024-09-30",
                        "category": "農產品",
                        "supply_type": "產地",
                        "product_type": "水果",
                        "products": [
                            {
                                "date": "2024-09-30",
                                "product_name": "香蕉",
                                "average_price": 10.0
                            }
                        ]
                    }
                ],
                "weekday": 1,
                "prev_day_is_holiday": True
            }
        ]
    })
