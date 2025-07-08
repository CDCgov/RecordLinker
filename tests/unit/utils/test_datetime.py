import datetime

from recordlinker.utils.datetime import now_utc


class TestNowUTC:
    def test(self):
        assert isinstance(now_utc(), datetime.datetime)
        assert now_utc().tzinfo is datetime.timezone.utc
        assert abs((now_utc() - datetime.datetime.now(datetime.timezone.utc)).total_seconds()) < 1

    def test_no_microseconds(self):
        assert now_utc(use_microseconds=False).microsecond == 0
