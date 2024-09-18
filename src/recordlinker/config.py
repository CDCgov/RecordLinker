import typing

import pydantic
import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8',
    )

    db_uri: str = pydantic.Field(description="The URI for the MPI database")
    connection_pool_size: typing.Optional[int] = pydantic.Field(
        description="The number of MPI database connections in the connection pool",
        default=5,
    )
    connection_pool_max_overflow: typing.Optional[int] = pydantic.Field(
        description="The maximum number of MPI database connections that can be opened "
        "above the connection pool size",
        default=10,
    )


settings = Settings()
