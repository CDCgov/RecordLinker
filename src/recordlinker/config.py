import logging.config
import typing

import pydantic
import pydantic_settings

from recordlinker.utils import path as utils


class ConfigurationError(Exception):
    """
    Error raised when there is a configuration issue.
    """

    pass


class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_uri: str = pydantic.Field(description="The URI for the MPI database")
    db_table_prefix: str = pydantic.Field(
        description="The prefix for all database tables",
        default="",
    )
    test_db_uri: str = pydantic.Field(
        description="The URI for the MPI database to run tests against",
        default="sqlite:///testdb.sqlite3",
    )
    connection_pool_size: typing.Optional[int] = pydantic.Field(
        description="The number of MPI database connections in the connection pool",
        default=None,
    )
    connection_pool_max_overflow: typing.Optional[int] = pydantic.Field(
        description="The maximum number of MPI database connections that can be opened "
        "above the connection pool size",
        default=None,
    )
    log_config: typing.Optional[str] = pydantic.Field(
        description="The path to the logging configuration file",
        default="",
    )
    splunk_uri: typing.Optional[str] = pydantic.Field(
        description="The URI for the Splunk HEC server",
        default="",
    )
    initialize_tables: bool = pydantic.Field(
        description="Create the database tables on startup if the database is empty",
        default=True,
    )
    initial_algorithms: str = pydantic.Field(
        description=(
            "The path to the initial algorithms file that is loaded on startup if the "
            "algorithms table is empty.  This file should be in JSON format.  If the "
            "value is an empty string, no algorithms will be loaded."
        ),
        default="assets/initial_algorithms.json",
    )
    api_root_path: str = pydantic.Field(
        description="The root path for the API",
        default="/api",
    )
    tuning_enabled: bool = pydantic.Field(
        description="Enable tuning",
        default=False,
    )
    tuning_true_match_pairs: int = pydantic.Field(
        description="The number of true match pairs to use for training",
        default=10000,
    )
    tuning_non_match_pairs: int = pydantic.Field(
        description="The number of non-match pairs to use for training",
        default=100000,
    )
    tuning_non_match_sample: int = pydantic.Field(
        description="The number of records to sample for non-match pairs",
        default=250000,
    )
    tuning_job_timeout: int = pydantic.Field(
        description="The number of seconds to wait for the tuning job to complete",
        default=3600,
    )

    def default_log_config(self) -> dict:
        """
        Return the default logging configuration.
        """
        return {
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
                "alembic": {"handlers": ["console"], "level": "INFO", "propagate": False},
                "recordlinker": {"handlers": ["console"], "level": "INFO", "propagate": False},
                "recordlinker.access": {
                    "handlers": ["console"],
                    "level": "CRITICAL",
                    "propagate": False,
                },
            },
        }

    def configure_logging(self) -> None:
        """
        Configure logging based on the provided configuration file. If no configuration
        file is provided, use the default configuration.
        """
        config = None
        if self.log_config:
            # Load logging config from the provided file
            try:
                config = utils.read_json(self.log_config)
            except Exception as exc:
                msg = f"Error loading log configuration: {self.log_config}"
                raise ConfigurationError(msg) from exc
        logging.config.dictConfig(config or self.default_log_config())

    @pydantic.field_validator("api_root_path", mode="before")
    @classmethod
    def normalize_api_root_path(cls, val: str) -> str:
        """
        Normalize the API root path.
        """
        if val is not None:
            if not val.startswith("/"):
                val = f"/{val}"
            if len(val) > 1 and val.endswith("/"):
                val = val[:-1]
            if val == "/":
                raise ValueError("API root path cannot be '/'")
        return val


settings = Settings()  # type: ignore
settings.configure_logging()
