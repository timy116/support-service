from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Union

import fitz
import pandas as pd

from app.core.enums import FileTypes, ProductType, DailyReportType, WeekDay


class FileReader(ABC):
    @abstractmethod
    def read(self, file_path: str) -> Union[dict, str]:
        pass


class PDFReader(FileReader):
    def read(self, file_path: str):
        with fitz.open(file_path) as doc:
            text = "".join(page.get_text() for page in doc)
        return text


class DailyReportReader:
    def __init__(
            self,
            date: date,
            product_type: ProductType,
            date_of_holidays: Union[list[date], None] = None
    ):
        self.roc_year = date.year - 1911
        self.date = date
        self.product_type = product_type
        self.date_of_holidays = date_of_holidays
        self._filename = None

    @property
    def filename(self) -> str:
        if self._filename is None:
            weekday = WeekDay(self.date.isoweekday())
            report_date = self._get_calculated_report_date(weekday)

            if report_date is None:
                return ""

            filenames = {
                ProductType.FRUIT: DailyReportType.FRUIT.value.format(
                    roc_year=self.roc_year, month=str(report_date.month).zfill(2), day=str(report_date.day).zfill(2)
                ),
                ProductType.FISH: DailyReportType.FISHERY.format(
                    roc_year=self.roc_year, month=self.date.month, day=self.date.day
                ),
            }
            self._filename = filenames.get(self.product_type, "")

        return self._filename

    def _get_calculated_report_date(self, weekday: WeekDay) -> Union[date, None]:
        prev_day_is_holiday = self.date - timedelta(days=1) in self.date_of_holidays

        if weekday is weekday.MONDAY:
            return self.date - timedelta(days=-2)

        return None if prev_day_is_holiday else self.date


class DailyReportPDFReader(PDFReader, DailyReportReader):
    def __init__(
            self, date: date,
            product_type: ProductType,
            date_of_holidays: Union[list[date], None] = None
    ):
        super().__init__(date, product_type)
        DailyReportReader.__init__(self, date, product_type, date_of_holidays)
        self.product_type = product_type
        self.date = date
        self.doc: Union[fitz.Document, None] = None

    @staticmethod
    def get_daily_report_reader(
            date: date, product_type: ProductType, date_of_holidays: Union[list[date], None] = None
    ) -> PDFReader:
        reader = {
            ProductType.FRUIT: FruitDailyReportPDFReader(date, product_type, date_of_holidays),
            ProductType.FISH: FishDailyReportPDFReader(date, product_type, date_of_holidays)
        }

        return reader.get(product_type, DailyReportPDFReader(date, product_type))

    def read(self, file_path: str):
        return self._extract_date_str_from_file_path(file_path)

    def _extract_date_str_from_file_path(self, file_path: str) -> dict:
        pass


class FruitDailyReportPDFReader(DailyReportPDFReader):
    QUERY = '產地 == "平均" and 產品別.str.contains("產地價格監控")'

    def _extract_date_str_from_file_path(self, file_path: str) -> dict:
        try:
            self.doc = fitz.open(file_path)
            df_tables_data = self._get_tables_data()

            return self._get_tables_data_into_dict(df_tables_data)
        finally:
            self.doc.close()

    def _get_tables_data(self) -> pd.DataFrame:
        df = pd.DataFrame()

        for i in range(self.doc.page_count):
            page = self.doc.load_page(i)
            tables = page.find_tables()
            df = pd.concat([df, tables[0].to_pandas()])

        return df

    def _get_tables_data_into_dict(self, df: pd.DataFrame) -> dict:
        selected_cols = self._get_selected_columns()
        df['產品別'] = df['產品別'].ffill()
        result = df \
            .query(self.QUERY) \
            .replace('－', 0) \
            .reset_index(drop=True)[selected_cols]

        for col in selected_cols:
            if col == '產品別':
                result[col] = result[col].apply(lambda x: str(x).split('\n')[0])
            else:
                result[col] = result[col].apply(lambda x: float(str(x).split('\n')[0]))

        return result.to_dict(orient='records')

    def _get_selected_columns(self) -> list[str]:
        time_delta = 1
        product_date = self.date - timedelta(days=1)
        selected_columns = []
        flag = True

        while flag:
            product_date = product_date - timedelta(days=1)
            is_holiday = product_date in self.date_of_holidays
            weekday = WeekDay(product_date.isoweekday())

            if weekday is WeekDay.SATURDAY or weekday is WeekDay.SUNDAY:
                time_delta += 1
            elif is_holiday:
                time_delta += 1
            else:
                flag = False

        for i in range(1, time_delta + 1):
            dt = product_date + timedelta(days=i)
            selected_columns.append(f"{dt.month}/{dt.day}")

        return ["產品別"] + selected_columns


class FishDailyReportPDFReader(DailyReportPDFReader):
    def _extract_date_str_from_file_path(self, file_path: str):
        pass


class ExcelReader(FileReader):
    def read(self, file_path: str) -> str:
        df = pd.read_excel(file_path)
        return df.to_string()


class TxtReader(FileReader):
    def read(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()


class FileReaderFactory:
    @classmethod
    def get_reader(
            cls,
            date: date,
            file_type: FileTypes,
            product_type: Union[ProductType, None] = None,
            date_of_holidays: Union[list[date], None] = None

    ) -> FileReader:
        readers = {
            FileTypes.PDF: cls.get_pdf_reader(date, product_type, date_of_holidays=date_of_holidays),
            FileTypes.EXCEL: ExcelReader(),
            FileTypes.TXT: TxtReader()
        }

        # default reader is PDFReader
        return readers.get(file_type, PDFReader())

    @staticmethod
    def get_pdf_reader(
            date: date,product_type: ProductType, date_of_holidays: Union[list[date], None] = None
    ) -> PDFReader:
        if product_type is not None:
            return DailyReportPDFReader.get_daily_report_reader(date, product_type, date_of_holidays=date_of_holidays)
        else:
            # default reader is PDFReader
            return PDFReader()


class DocumentProcessor:
    def __init__(
            self,
            date: date,
            file_type: FileTypes,
            product_type: Union[ProductType, None] = None,
            date_of_holidays: Union[list[date], None] = None
    ):
        self.reader = FileReaderFactory.get_reader(
            date,
            file_type,
            product_type=product_type,
            date_of_holidays=date_of_holidays
        )
        self.file_type = file_type

    def process(self, file_path: str) -> Union[dict, str]:
        return self.reader.read(file_path)
