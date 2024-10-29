# Configuration


## Application Configuration

The RecordLinker application is configured via a
[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
configuration class. The settings are loaded from environment variables or a `.env` file,
allowing for easy customization without modifying the code.  When both an environment 
variable and a `.env` file are present, the environment variable takes precedence.


### Configuration Settings and Descriptions

Each setting can be configured as follows:

`db_uri (Required)`

:   The URI for the application database.

    Example: `postgresql://user:password@localhost/dbname`

`db_table_prefix (Optional)`

:   Prefix applied to all database tables, useful for namespace separation.

    Docker Default: `""`
    Development Default: `""`

`test_db_uri (Optional)`

:   The URI for the application database used when running tests.

    Docker Default: `sqlite:///testdb.sqlite3`
    Development Default: `sqlite:///testdb.sqlite3`

`connection_pool_size (Optional)`

:   Number of connections in the MPI database connection pool.

    Docker Default: `5`
    Development Default: `5`

`connection_pool_max_overflow (Optional)`

:   Maximum number of overflow connections allowed in the connection pool.

    Docker Default: `10`
    Development Default: `10`

`log_config (Optional)`

:   Path to a logging configuration file, used to configure logging settings on startup.
    A value of an empty string will cause logging to use default settings.

    Docker Default: `"assets/production_log_config.json"`
    Development Default: `""`

`initial_algorithms (Optional)`

:   Path to a JSON file with initial algorithms to load if the algorithms table is empty.

    Docker Default: `assets/initial_algorithms.json`
    Default: `assets/initial_algorithms.json`


## Docker Configuration


