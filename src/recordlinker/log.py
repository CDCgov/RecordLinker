import json
import logging
import typing

import pythonjsonlogger.jsonlogger

from recordlinker import config
from recordlinker import splunk

RESERVED_ATTRS = pythonjsonlogger.jsonlogger.RESERVED_ATTRS + ("taskName",)


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


class JSONFormatter(pythonjsonlogger.jsonlogger.JsonFormatter):
    """
    A custom JSON formatter that excldues the taskName field by default.
    """

    def __init__(
        self,
        *args: typing.Any,
        reserved_attrs: tuple[str, ...] = RESERVED_ATTRS,
        **kwargs: typing.Any,
    ):
        super().__init__(*args, reserved_attrs=reserved_attrs, **kwargs)


class SplunkHecHandler(logging.Handler):
    """
    A custom logging handler that sends log records to a Splunk HTTP Event Collector (HEC)
    server. This handler is only enabled if the `splunk_uri` setting is configured,
    otherwise each log record is ignored.
    """

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

    def __init__(self, **kwargs: typing.Any) -> None:
        logging.Handler.__init__(self)
        self.client: splunk.SplunkHECClient | None = None
        if config.settings.splunk_uri:
            self.client = self.SplunkHecClientSingleton.get_instance(config.settings.splunk_uri)

    def emit(self, record: logging.log) -> None:
        """
        Emit the log record to the Splunk HEC server, if a client is configured.
        """
        if self.client is None:
            # No Splunk HEC client configured, do nothing
            return
        msg = self.format(record)
        try:
            # Attempt to parse the message as a JSON object
            msg = json.loads(msg)
        except json.JSONDecodeError:
            # If the message is not JSON, create a new dictionary with the message
            msg = {"message": msg}
        self.client.send(msg, epoch=record.created)
