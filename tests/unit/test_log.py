import logging
import unittest.mock

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


class TestSplunkHecHandler:
    def test_json_record(self):
        with unittest.mock.patch("recordlinker.splunk.SplunkHECClient") as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.send.return_value = 200
            uri = "splunkhec://token@localhost:8088?index=index&source=source"
            handler = log.SplunkHecHandler(uri=uri)
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test_log.py",
                lineno=10,
                exc_info=None,
                msg='{"key": "value"}',
                args=[],
            )
            assert handler.emit(record) is None
            handler.flush()
            send_args = mock_instance.send.call_args.args
            assert send_args == ({"key": "value"},)
            send_kwargs = mock_instance.send.call_args.kwargs
            assert send_kwargs == {"epoch": record.created}
            log.SplunkHecHandler.SplunkHecClientSingleton._instance = None

    def test_non_json_record(self):
        with unittest.mock.patch("recordlinker.splunk.SplunkHECClient") as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.send.return_value = 200
            uri = "splunkhec://token@localhost:8088?index=index&source=source"
            handler = log.SplunkHecHandler(uri=uri)
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test_log.py",
                lineno=10,
                exc_info=None,
                msg="test",
                args=[],
            )
            assert handler.emit(record) is None
            handler.flush()
            send_args = mock_instance.send.call_args.args
            assert send_args == ({"message": "test"},)
            send_kwargs = mock_instance.send.call_args.kwargs
            assert send_kwargs == {"epoch": record.created}
            log.SplunkHecHandler.SplunkHecClientSingleton._instance = None
