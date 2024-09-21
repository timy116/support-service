from datetime import datetime, timedelta


def get_datetime_utc_8():
    return datetime.now() + timedelta(hours=8)


def get_date():
    return get_datetime_utc_8().date()


def datetime_format(datetime_str: str):
    if len(datetime_str) == 8:
        formatted_date = datetime.strptime(datetime_str, "%Y%m%d").date()
    elif datetime_str.find('-') == 3:
        formatted_date = datetime.strptime(datetime_str, "%Y-%m-%d").date()
    elif datetime_str.find('/') == 3:
        formatted_date = datetime.strptime(datetime_str, "%Y/%m/%d").date()
    elif datetime_str.find('.') == 3:
        formatted_date = datetime.strptime(datetime_str, "%Y.%m.%d").date()
    else:
        raise ValueError("Invalid date format")
    return formatted_date
