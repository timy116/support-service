import requests
from requests import Response

from app.core.enums import OpenApis


class TaiwanCalendarApi:

    def __init__(self, year: int, size: int = 1000, formant: str = "json"):
        self.url: str = OpenApis.TAIWAN_CALENDAR_API
        self.formant: str = formant
        self.params: dict = {
            "year": year,
            "size": size
        }

    def get(self) -> Response:
        return requests.api.get(f"{self.url}/{self.formant}", params=self.params).json()
