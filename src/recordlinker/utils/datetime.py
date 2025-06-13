import datetime


def now_utc():
    """
    Get the current time in UTC.
    """
    return datetime.datetime.now(datetime.timezone.utc)
