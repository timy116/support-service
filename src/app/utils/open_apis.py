import requests

from app.core.enums import OpenApis, IsNotHolidays


class TaiwanCalendarApi:

    def __init__(self, year: int, size: int = 1000, formant: str = "json"):
        self.url: str = OpenApis.TAIWAN_CALENDAR_API
        self.formant: str = formant
        self.params: dict = {
            "year": year,
            "size": size
        }

    @property
    async def cleaned_list(self) -> list[dict]:
        json = await self.get()
        _list = []

        for d in json:
            try:
                if d["name"] is not None:
                    IsNotHolidays(d["name"])
            except ValueError:
                _list.append(d)

        return _list

    async def get(self):
        return requests.api.get(f"{self.url}/{self.formant}", params=self.params).json()
