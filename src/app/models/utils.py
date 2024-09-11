from datetime import datetime, timedelta


def get_datetime_utc_8():
    return datetime.now() + timedelta(hours=8)
