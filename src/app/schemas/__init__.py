from beanie.odm.documents import json_schema_extra
from pydantic import ConfigDict

from .daily_reports import DailyReport
from .pagination import Paginated, PaginationParams
from .sorting import SortingParams
from ..core.enums import WeekDay


class PaginatedDailyReport(Paginated):
    weekday: WeekDay
    prev_day_is_holiday: bool
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
