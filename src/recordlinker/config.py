import typing

import pydantic
import pydantic_settings


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
    initial_algorithms: str = pydantic.Field(
        description=(
            "The path to the initial algorithms file that is loaded on startup if the "
            "algorithms table is empty.  This file should be in JSON format.  If the "
            "value is an empty string, no algorithms will be loaded.",
        ),
        default="assets/initial_algorithms.json",
    )


settings = Settings()  # type: ignore
