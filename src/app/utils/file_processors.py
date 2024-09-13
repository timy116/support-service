from abc import ABC, abstractmethod

import fitz
import pandas as pd

from app.core.enums import FileTypes


class FileReader(ABC):
    @abstractmethod
    def read(self, file_path: str) -> str:
        pass


class PDFReader(FileReader):
    def read(self, file_path: str) -> str:
        with fitz.open(file_path) as doc:
            text = "".join(page.get_text() for page in doc)
        return text


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
    def get_reader(file_type: FileTypes) -> FileReader:
        readers = {
            FileTypes.PDF: PDFReader(),
            FileTypes.EXCEL: ExcelReader(),
            FileTypes.TXT: TxtReader()
        }

        # default reader is PDFReader
        return readers.get(file_type, PDFReader())


class DocumentProcessor:
    def __init__(self, file_type: FileTypes):
        self.reader = FileReaderFactory.get_reader(file_type)
        self.file_type = file_type

    def process(self, file_path: str) -> str:
        return self.reader.read(file_path)
