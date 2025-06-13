import datetime
import functools


def now_utc(use_microseconds: bool = True) -> datetime.datetime:
    """
    Get the current time in UTC.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    if not use_microseconds:
        now = now.replace(microsecond=0)
    return now

now_utc_no_ms = functools.partial(now_utc, use_microseconds=False)
