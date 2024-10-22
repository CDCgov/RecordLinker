import logging
import typing

import pythonjsonlogger.jsonlogger

RESERVED_ATTRS = pythonjsonlogger.jsonlogger.RESERVED_ATTRS + ("taskName",)

DEFAULT_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"key_value": {"()": "recordlinker.log.KeyValueFilter"}},
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s [%(asctime)s] ... %(message)s",
            "datefmt": "%H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "filters": ["key_value"],
            "stream": "ext://sys.stderr",
        }
    },
    "loggers": {
        "": {"handlers": ["console"], "level": "WARNING"},
        "recordlinker": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "recordlinker.access": {"handlers": ["console"], "level": "CRITICAL", "propagate": False},
    },
}


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
