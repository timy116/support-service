import re
from abc import ABC, abstractmethod
from typing import Union

import fitz
import pandas as pd
from pandas.core.interchange.dataframe_protocol import DataFrame

from app.core.enums import FileTypes, ProductType


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


class DailyReportPDFReader(PDFReader):
    def __init__(self, product_type: ProductType):
        super().__init__()
        self.product_type = product_type
        self.date_str = ''

    def read(self, file_path: str, product_type: Union[ProductType, None] = None) -> Union[DataFrame, str]:
        self._extract_date_str_from_file_path(file_path)

        return super().read(file_path, product_type)

    def _extract_date_str_from_file_path(self, file_path: str):
        file_name = file_path.split('/')[-1].split('_')[0]

        # e.g. ['113', '9', '13'] -> 113/9/13
        date_str = '/'.join([str(int(i)) for i in re.findall('\d+', file_name)])

        if date_str and len(date_str.split('/')) == 3:
            # e.g. 113/9/13 -> 9/13
            self.date_str = f'{date_str[1]}/{date_str[2]}'


class ExcelReader(FileReader):
    def read(self, file_path: str) -> str:
        df = pd.read_excel(file_path)
        return df.to_string()


class TxtReader(FileReader):
    def read(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()


class FileReaderFactory:
    @staticmethod
    def get_reader(file_type: FileTypes, product_type: Union[ProductType, None] = None) -> FileReader:
        readers = {
            FileTypes.PDF: FileReaderFactory.get_pdf_reader(product_type),
            FileTypes.EXCEL: ExcelReader(),
            FileTypes.TXT: TxtReader()
        }

        # default reader is PDFReader
        return readers.get(file_type, PDFReader())

    @staticmethod
    def get_pdf_reader(product_type: Union[ProductType, None] = None) -> PDFReader:
        if product_type is not None:
            return DailyReportPDFReader(product_type)
        else:
            # default reader is PDFReader
            return PDFReader()


class DocumentProcessor:
    def __init__(self, file_type: FileTypes):
        self.reader = FileReaderFactory.get_reader(file_type)
        self.file_type = file_type

    def process(self, file_path: str) -> str:
        return self.reader.read(file_path)
