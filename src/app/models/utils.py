from datetime import datetime

import pytz


def get_datetime_utc_8():
    return datetime.now(pytz.timezone('Asia/Taipei'))
