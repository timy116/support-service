from abc import ABC, abstractmethod
from datetime import timedelta, datetime
from typing import Union

import fitz
import pandas as pd

from app.core.enums import (
    FileTypes,
    ProductType,
    DailyReportType,
    WeekDay,
    SupplyType,
    Category,
)


class FileReader(ABC):
    """
    `FileReader` is an abstract class that defines the interface for reading files.
    """

    @abstractmethod
    def read(self, file_path: str) -> Union[list, str]:
        pass


class PDFReader(FileReader):
    """
    `PDFReader` is a class that reads the content of a PDF file.
    """

    def read(self, file_path: str):
        with fitz.open(file_path) as doc:
            text = "".join(page.get_text() for page in doc)
        return text


class DailyReportMetaInfo:
    """
    `DailyReportMetaInfo` is a class that contains the meta information of the daily report.
    """

    def __init__(
            self,
            date: datetime.date,
            product_type: ProductType,
            date_of_holidays: Union[list[datetime.date], None] = None
    ):
        """
        :param date: The date of the daily report.
        :param product_type: The type of the product.
        :param date_of_holidays: The list of holidays.
        """

        self.roc_year = date.year - 1911
        self.date = date
        self.product_type = product_type
        self.date_of_holidays = date_of_holidays
        self._filename = None

    @property
    def filename(self) -> str:
        """
        The filename of the daily report, it is calculated based on the date and product type.
        Also, the filename is used to get email for searching the daily report.

        :return: The filename of the daily report.
        """
        if self._filename is None:
            weekday = WeekDay(self.date.isoweekday())
            report_date = self._get_calculated_report_date(weekday)

            if report_date is None:
                return ""

            # The filename of the daily report is different based on the product type.
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

    def _get_calculated_report_date(self, weekday: WeekDay) -> Union[datetime.date, None]:
        """
        Get the calculated report date based on the weekday.

        :param weekday: The weekday of the date.
        :return: The calculated report date.
        """
        prev_day_is_holiday = self.date - timedelta(days=1) in self.date_of_holidays

        if weekday is weekday.MONDAY:
            # Saturday will receive the report of the previous Friday.
            return self.date - timedelta(days=-2)

        return None if prev_day_is_holiday else self.date


class DailyReportPDFReader(PDFReader, DailyReportMetaInfo):
    """
    `DailyReportPDFReader` is a class that reads the content of the daily report in PDF format.
    """

    def __init__(
            self,
            date: datetime.date,
            product_type: ProductType,
            date_of_holidays: Union[list[datetime.date], None] = None
    ):
        super().__init__(date, product_type)
        DailyReportMetaInfo.__init__(self, date, product_type, date_of_holidays)
        self.supply_type: Union[SupplyType, None] = None
        self.category: Union[Category, None] = None
        self.product_type = product_type
        self.date = date
        self.doc: Union[fitz.Document, None] = None
        self._selected_columns = None

    @property
    def supply_type(self) -> SupplyType:
        return self._supply_type

    @supply_type.setter
    def supply_type(self, value: SupplyType):
        self._supply_type = value

    @property
    def category(self) -> Category:
        return self._category

    @category.setter
    def category(self, value: Category):
        self._category = value

    @staticmethod
    def get_daily_report_reader(
            date: datetime.date, product_type: ProductType, date_of_holidays: Union[list[datetime.date], None] = None
    ) -> PDFReader:
        """
        This method is used to get the essential daily report reader based on the product type.
        :return: The daily report reader.
        """
        reader = {
            ProductType.FRUIT: FruitDailyReportPDFReader(date, product_type, date_of_holidays),
            ProductType.FISH: FishDailyReportPDFReader(date, product_type, date_of_holidays)
        }

        return reader.get(product_type, DailyReportPDFReader(date, product_type))

    def read(self, file_path: str):
        return self._extract_data_from_file(file_path)

    def _extract_data_from_file(self, file_path: str) -> list:
        pass


class FruitDailyReportPDFReader(DailyReportPDFReader):
    """
    `FruitDailyReportPDFReader` is a class that "only" reads the content of the daily report of the fruit in PDF format.
    """
    QUERY = '產地 == "平均" and 產品別.str.contains("產地價格監控")'
    PRODUCT_COLUMN = '產品別'

    def __init__(
            self,
            date: datetime.date,
            product_type: ProductType,
            date_of_holidays: Union[list[datetime.date], None] = None
    ):
        super().__init__(date, product_type, date_of_holidays)
        self.supply_type = SupplyType.ORIGIN
        self.category = Category.AGRICULTURE

    @property
    def prev_day_is_holiday(self) -> bool:
        weekday = WeekDay(self.date.isoweekday())

        return (
                weekday is WeekDay.SATURDAY
                or WeekDay is WeekDay.SUNDAY
                or self.date - timedelta(days=1) in self.date_of_holidays
        )

    @property
    def selected_columns(self) -> list[str]:
        if self._selected_columns is None:
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

            self._selected_columns = [self.PRODUCT_COLUMN] + selected_columns

        return self._selected_columns

    def _extract_date_str_from_file_path(self, file_path: str):
        try:
            self.doc = fitz.open(file_path)
            df_tables_data = self._get_tables_data()

            # call the other method to get the data into a dictionary.
            return self._get_tables_data_into_dict(df_tables_data)
        finally:
            # close the document after reading the content whether it is successful or not.
            self.doc.close()

    def _get_tables_data(self) -> pd.DataFrame:
        """
        Get the tables data from the PDF document and convert it to a pandas DataFrame.

        :return: The tables data as a pandas DataFrame.
        """
        df = pd.DataFrame()

        # iterate over the pages of the document and get the tables' data.
        for i in range(self.doc.page_count):
            page = self.doc.load_page(i)
            tables = page.find_tables()
            df = pd.concat([df, tables[0].to_pandas()])

        return df

    def _get_tables_data_into_dict(self, df: pd.DataFrame) -> list:
        """
        Get the tables' data into a dictionary.

        :param df: The tables' data already converted to a pandas DataFrame.
        :return: A list of dictionaries that contain the tables' data.
        """
        df[self.PRODUCT_COLUMN] = df[self.PRODUCT_COLUMN].ffill()
        result = df \
            .query(self.QUERY) \
            .replace('－', 0) \
            .reset_index(drop=True)[self.selected_columns]

        # clean the data and convert it to the correct type.
        for col in self.selected_columns:
            if col == self.PRODUCT_COLUMN:
                result[col] = result[col].apply(lambda x: str(x).split('\n')[0])
            else:
                result[col] = result[col].apply(lambda x: float(str(x).split('\n')[0]))

        return result.to_dict(orient='records')


class FishDailyReportPDFReader(DailyReportPDFReader):
    def _extract_data_from_file(self, file_path: str):
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
    """
    `FileReaderFactory` is a class that creates the reader based on the file type by
    using the simple factory pattern.
    """

    @classmethod
    def get_reader(
            cls,
            date: datetime.date,
            file_type: FileTypes,
            product_type: Union[ProductType, None] = None,
            date_of_holidays: Union[list[datetime.date], None] = None

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
            date: datetime.date, product_type: ProductType, date_of_holidays: Union[list[datetime.date], None] = None
    ) -> PDFReader:
        """
        Get the PDF reader based on the product type.
        :return: The PDF reader.
        """
        if product_type is not None:
            return DailyReportPDFReader.get_daily_report_reader(date, product_type, date_of_holidays=date_of_holidays)
        else:
            # default reader is PDFReader
            return PDFReader()


class DocumentProcessor:
    """
    `DocumentProcessor` is a class that processes the document based on the file type.
    """

    def __init__(
            self,
            date: datetime.date,
            file_type: FileTypes,
            product_type: Union[ProductType, None] = None,
            date_of_holidays: Union[list[datetime.date], None] = None
    ):
        self.reader = FileReaderFactory.get_reader(
            date,
            file_type,
            product_type=product_type,
            date_of_holidays=date_of_holidays
        )
        self.file_type = file_type

    def process(self, file_path: str) -> Union[dict, str]:
        """
        Process the document based on the file type.

        :return: The processed document as a dictionary or a string.
        """
        return self.reader.read(file_path)
