import datetime

from recordlinker.utils.datetime import now_utc


def test_now_utc():
    assert isinstance(now_utc(), datetime.datetime)
    assert now_utc().tzinfo is datetime.timezone.utc
    assert abs((now_utc() - datetime.datetime.now(datetime.timezone.utc)).total_seconds()) < 1
