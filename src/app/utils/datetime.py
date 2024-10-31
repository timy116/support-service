import platform
import re
from datetime import datetime, timedelta
from enum import StrEnum


class OsNames(StrEnum):
    WINDOWS = 'Windows'
    LINUX = 'Linux'
    MACOS = 'Darwin'


def get_datetime_utc_8():
    return datetime.now() + timedelta(hours=8) if OsNames(platform.system()) in OsNames.LINUX else datetime.now()


def get_date():
    return datetime.now().date()


def datetime_formatter(datetime_str: str):
    def transform_date(date_str, sep):
        return sep.join([str(int(part) + 1911) if len(part) == 3 else part.zfill(2) for part in date_str.split(sep)])

    if re.match(r'^\d{8}$', datetime_str):
        return datetime.strptime(datetime_str, "%Y%m%d").date()
    if re.match(r'^\d{7}$', datetime_str) and not datetime_str.startswith('20'):
        return datetime.strptime(str(int(datetime_str[:3]) + 1911) + datetime_str[3:], "%Y%m%d").date()
    if '-' in datetime_str:
        return datetime.strptime(transform_date(datetime_str, '-'), "%Y-%m-%d").date()
    if '/' in datetime_str:
        return datetime.strptime(transform_date(datetime_str, '/'), "%Y/%m/%d").date()
    if '.' in datetime_str:
        return datetime.strptime(transform_date(datetime_str, '.'), "%Y.%m.%d").date()

    raise ValueError("Invalid date format")
