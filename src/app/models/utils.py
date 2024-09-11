from datetime import datetime, timedelta


def get_datetime_utc_8():
    return datetime.now() + timedelta(hours=8)

def get_date():
    return get_datetime_utc_8().date()
