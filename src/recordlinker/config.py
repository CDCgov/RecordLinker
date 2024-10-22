import logging
import typing

import pydantic
import pydantic_settings

from recordlinker import utils


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
    test_db_uri: str = pydantic.Field(
        description="The URI for the MPI database to run tests against",
        default="sqlite:///testdb.sqlite3",
    )
    connection_pool_size: typing.Optional[int] = pydantic.Field(
        description="The number of MPI database connections in the connection pool",
        default=5,
    )
    connection_pool_max_overflow: typing.Optional[int] = pydantic.Field(
        description="The maximum number of MPI database connections that can be opened "
        "above the connection pool size",
        default=10,
    )
    log_config: typing.Optional[str] = pydantic.Field(
        description="The path to the logging configuration file",
        default="assets/development_log_config.json"
    )
    initial_algorithms: str = pydantic.Field(
        description=(
            "The path to the initial algorithms file that is loaded on startup if the "
            "algorithms table is empty.  This file should be in JSON format.  If the "
            "value is an empty string, no algorithms will be loaded."
        ),
        default="assets/initial_algorithms.json",
    )

    @pydantic.field_validator("log_config", mode="before")
    def validate_log_config(cls, value):
        """
        Validate the log_config value.
        """
        try:
            config = utils.read_json(value)
            logging.config.dictConfig(config)
        except Exception as exc:
            raise ConfigurationError(f"Error loading log configuration: {value}") from exc
        return value


settings = Settings()  # type: ignore
