from abc import ABC, abstractmethod
from datetime import date
from typing import Union

import fitz
import pandas as pd
from pandas import DataFrame

from app.core.enums import FileTypes, ProductType, DailyReportType


class FileReader(ABC):
    @abstractmethod
    def read(self, file_path: str) -> str:
        pass


class PDFReader(FileReader):
    def read(self, file_path: str, product_type: Union[ProductType, None] = None) -> Union[DataFrame, str]:
        with fitz.open(file_path) as doc:
            print(f'the PDF file path: {file_path}')
            text = "".join(page.get_text() for page in doc)
        return text


class DailyReportReader:
    def __init__(self, date: date, product_type: ProductType):
        self.roc_year = date.year - 1911
        self.date = date
        self.product_type = product_type
        self.filename: str = self._get_filename()

    def _get_filename(self):
        filenames = {
            ProductType.FRUIT: DailyReportType.FRUIT.value.format(
                roc_year=self.roc_year, month=self.date.month, day=self.date.day
            ),
            ProductType.FISH: DailyReportType.FISHERY.format(
                roc_year=self.roc_year, month=self.date.month, day=self.date.day
            ),
        }

        return filenames.get(self.product_type)


class DailyReportPDFReader(PDFReader, DailyReportReader):
    def __init__(self, date: date, product_type: ProductType):
        super().__init__(date, product_type)
        self.product_type = product_type
        self.date = date

    @staticmethod
    def get_daily_report_reader(date: date, product_type: ProductType) -> PDFReader:
        reader = {
            ProductType.FRUIT: FruitDailyReportPDFReader(date, product_type),
            ProductType.FISH: FishDailyReportPDFReader(date, product_type)
        }

        return reader.get(product_type, DailyReportPDFReader(date, product_type))

    def read(self, file_path: str, product_type: Union[ProductType, None] = None) -> Union[DataFrame, str]:
        self._extract_date_str_from_file_path(file_path)

        return super().read(file_path, product_type)

    def _extract_date_str_from_file_path(self, file_path: str):
        pass


class FruitDailyReportPDFReader(DailyReportPDFReader):
    def _extract_date_str_from_file_path(self, file_path: str):
        pass


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
    def get_reader(cls, date: date, file_type: FileTypes, product_type: Union[ProductType, None] = None) -> FileReader:
        readers = {
            FileTypes.PDF: cls.get_pdf_reader(date, product_type),
            FileTypes.EXCEL: ExcelReader(),
            FileTypes.TXT: TxtReader()
        }

        # default reader is PDFReader
        return readers.get(file_type, PDFReader())

    @staticmethod
    def get_pdf_reader(date: date, product_type: Union[ProductType, None] = None) -> PDFReader:
        if product_type is not None:
            return DailyReportPDFReader.get_daily_report_reader(date, product_type)
        else:
            # default reader is PDFReader
            return PDFReader()


class DocumentProcessor:
    def __init__(self, date: date, file_type: FileTypes, product_type: Union[ProductType, None] = None):
        self.reader = FileReaderFactory.get_reader(date, file_type, product_type)
        self.file_type = file_type

    def process(self, file_path: str) -> str:
        return self.reader.read(file_path)
