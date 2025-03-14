import concurrent.futures
import json
import logging
import typing

import pythonjsonlogger.core
import pythonjsonlogger.json

from recordlinker import config
from recordlinker import splunk

RESERVED_ATTRS = pythonjsonlogger.core.RESERVED_ATTRS + ["taskName"]


# Custom filter to transform log arguments into JSON fields
class DictArgFilter(logging.Filter):
    def filter(self, record):
        """
        Filter the log record to extract the dictionary arguments as fields.
        """
        # if the args are a dictionary, set the key-value pairs as attributes
        if isinstance(record.args, dict):
            for key, value in record.args.items():
                setattr(record, key, value)
        return True


class KeyValueFilter(logging.Filter):
    def filter(self, record):
        """
        Filter the log record to extract the key-value pairs from the log message.
        """
        for key, value in record.__dict__.items():
            if key not in RESERVED_ATTRS:
                record.msg = f"{record.msg} {key}={value}"
        return True


class JSONFormatter(pythonjsonlogger.json.JsonFormatter):
    """
    A custom JSON formatter that excldues the taskName field by default.
    """

    def __init__(
        self,
        *args: typing.Any,
        reserved_attrs: typing.Sequence[str] = RESERVED_ATTRS,
        **kwargs: typing.Any,
    ):
        super().__init__(*args, reserved_attrs=reserved_attrs, **kwargs)


class SplunkHecHandler(logging.Handler):
    """
    A custom logging handler that sends log records to a Splunk HTTP Event Collector (HEC)
    server. This handler is only enabled if the `splunk_uri` setting is configured,
    otherwise each log record is ignored.

    WARNING: This handler does not guarantee delivery of log records to the Splunk HEC
    server.  Events are sent asynchronously to reduce blocking IO calls, and the client
    does not wait for a response from the server.  Thus its possible that some log records
    will be dropped.  Other logging handlers should be used in conjunction with this handler
    in production environments to ensure log records are not lost.
    """

    MAX_WORKERS = 10

    class SplunkHecClientSingleton:
        """
        A singleton class for the Splunk HEC client.
        """

        _instance: splunk.SplunkHECClient | None = None

        @classmethod
        def get_instance(cls, uri: str) -> splunk.SplunkHECClient:
            """
            Get the singleton instance of the Splunk HEC client.
            """
            if cls._instance is None:
                cls._instance = splunk.SplunkHECClient(uri)
            return cls._instance

    def __init__(self, uri: str | None = None, **kwargs: typing.Any) -> None:
        """
        Initialize the Splunk HEC logging handler.  If the `splunk_uri` setting is
        configured, create a new Splunk HEC client instance or use the existing
        singleton instance.  Its optimal to use a singleton instance to avoid
        re-testing the connection to the Splunk HEC server.
        """
        logging.Handler.__init__(self)
        self.client: splunk.SplunkHECClient | None = None
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_WORKERS)
        self.last_future: concurrent.futures.Future | None = None
        uri = uri or config.settings.splunk_uri
        if uri:
            self.client = self.SplunkHecClientSingleton.get_instance(uri)

    def __del__(self) -> None:
        """
        Clean up the executor when the handler is deleted.
        """
        self.executor.shutdown(wait=True)

    def flush(self) -> None:
        """
        Wait for the last future to complete before flushing the handler.
        """
        if self.last_future is not None:
            self.last_future.result()
        self.last_future = None

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit the log record to the Splunk HEC server, if a client is configured.
        """
        if self.client is None:
            # No Splunk HEC client configured, do nothing
            return
        msg = self.format(record)
        data: dict[str, typing.Any] = {}
        try:
            # Attempt to parse the message as a JSON object
            data = json.loads(msg)
        except json.JSONDecodeError:
            # If the message is not JSON, create a new dictionary with the message
            data = {"message": msg}
        # Run this in a separate thread to avoid blocking the main thread.
        # Logging to Splunk is a bonus feature and should not block the main thread,
        # using a ThreadPoolExecutor to send the request asynchronously allows us
        # to initiate the request and continue processing without waiting for the IO
        # operation to complete.
        self.last_future = self.executor.submit(self.client.send, data, epoch=record.created)
