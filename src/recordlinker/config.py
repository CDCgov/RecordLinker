import json
import logging.config
import typing

import pydantic
import pydantic_settings

from recordlinker.log import DEFAULT_LOGGING_CONFIG


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
        default="",
    )
    initial_algorithms: str = pydantic.Field(
        description=(
            "The path to the initial algorithms file that is loaded on startup if the "
            "algorithms table is empty.  This file should be in JSON format.  If the "
            "value is an empty string, no algorithms will be loaded."
        ),
        default="assets/initial_algorithms.json",
    )

    def configure_logging(self) -> None:
        """
        Configure logging based on the provided configuration file. If no configuration
        file is provided, use the default configuration.
        """
        config = None
        if self.log_config:
            # Load logging config from the provided file
            try:
                with open(self.log_config, "r") as fobj:
                    config = json.loads(fobj.read())
            except Exception as exc:
                raise ConfigurationError(
                    f"Error loading log configuration: {self.log_config}"
                ) from exc
        logging.config.dictConfig(config or DEFAULT_LOGGING_CONFIG)


settings = Settings()  # type: ignore
settings.configure_logging()
