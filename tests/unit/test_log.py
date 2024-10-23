import logging

from recordlinker import log


class TestDictArgFilter:
    def test_filter(self):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test_log.py",
            lineno=10,
            exc_info=None,
            msg="test",
            args=[{"key": "value"}],
        )
        assert log.DictArgFilter().filter(record)
        assert record.key == "value"

    def test_no_dict_args(self):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test_log.py",
            lineno=10,
            exc_info=None,
            msg="test",
            args=["value"],
        )
        assert log.DictArgFilter().filter(record)
        assert not hasattr(record, "value")


class TestKeyValueFilter:
    def test_filter(self):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test_log.py",
            lineno=10,
            exc_info=None,
            msg="test",
            args=[],
        )
        record.key = "value"
        assert log.KeyValueFilter().filter(record)
        assert record.msg == "test key=value"

    def test_reserved_attrs(self):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test_log.py",
            lineno=10,
            exc_info=None,
            msg="test",
            args=[],
        )
        record.taskName = "task"
        assert log.KeyValueFilter().filter(record)
        assert record.msg == "test"


class TestJsonFormatter:
    def test_format(self):
        formatter = log.JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test_log.py",
            lineno=10,
            exc_info=None,
            msg="test",
            args=[],
        )
        assert formatter.format(record) == '{"message": "test"}'

    def test_format_reserved_attrs(self):
        formatter = log.JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test_log.py",
            lineno=10,
            exc_info=None,
            msg="test",
            args=[],
        )
        record.taskName = "task"
        assert formatter.format(record) == '{"message": "test"}'
