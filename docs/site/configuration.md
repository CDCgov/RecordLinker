# Configuration


## Application Configuration

The RecordLinker application is configured via a
[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
configuration class. The settings are loaded from environment variables or a `.env` file,
allowing for easy customization without modifying the code.  When both an environment 
variable and a `.env` file are present, the environment variable takes precedence.


### Configuration Settings

Each setting can be configured as follows:

`DB_URI (Required)`

:   The URI for the application database.

    Example: `postgresql+psycopg2://user:password@localhost/dbname`

`DB_TABLE_PREFIX (Optional)`

:   Prefix applied to all database tables, useful for namespace separation.

    **Docker Default**: `""`

    **Development Default**: `""`

`TEST_DB_URI (Optional)`

:   The URI for the application database used when running tests.

    **Docker Default**: `sqlite:///testdb.sqlite3`

    **Development Default**: `sqlite:///testdb.sqlite3`

`CONNECTION_POOL_SIZE (Optional)`

:   Number of connections in the MPI database connection pool.

    **Docker Default**: `5`

    **Development Default**: `5`

`CONNECTION_POOL_MAX_OVERFLOW (Optional)`

:   Maximum number of overflow connections allowed in the connection pool.

    **Docker Default**: `10`

    **Development Default**: `10`

`LOG_CONFIG (Optional)`

:   Path to a logging configuration file, used to configure logging settings on startup.
    A value of an empty string will cause logging to use default settings.

    **Docker Default**: `"assets/production_log_config.json"`

    **Development Default**: `""`

`SPLUNK_URI (Optional)`

:   URI for the Splunk HTTP Event Collector (HEC) endpoint. When set, logs will be sent to
    the configured Splunk instance for analysis. The format is
    `splunkhec://<token>@<host>:<port>?index=<index>&proto=<protocol>&source=<source>`

    **Docker Default**: `""`

    **Development Default**: `""`

`INITIAL_ALGORITHMS (Optional)`

:   Path to a JSON file with initial algorithms to load if the algorithms table is empty.

    **Docker Default**: `assets/initial_algorithms.json`

    **Development Default**: `assets/initial_algorithms.json`


### Database Options

The `DB_URI` and `TEST_DB_URI` settings can be configured to connect to a compatible
[SQLAlchemy](https://www.sqlalchemy.org/) database.  By default, the following database
drivers are installed allowing for connections to:

- **[sqlite3](https://docs.python.org/3/library/sqlite3.html) (sqlite)**

    Example: `sqlite:///db.sqlite3`

- **[psycopg2](https://www.psycopg.org/) (postgresql)**

    Example: `postgresql+psycopg2://user:password@localhost/dbname`

- **[pymysql](https://pymysql.readthedocs.io/en/latest/) (mysql)**

    Example: `mysql+pymysql://user:password@localhost/dbname`

- **[pyodbc](https://github.com/mkleehammer/pyodbc/wiki) (sqlite)**

    Example: `mssql+pyodbc://user:password@localhost/dbname?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes`


## Docker Configuration

In addition to the above application settings that can be configured via environment variables,
the Dockerfile can be built with the build arguments to customize the container.

`ENVIRONMENT (Optional)`

:   The environment to install python packages for.  Options are `dev` or `prod`, see the 
    `pyproject.toml` file for details on the list of packages installed for each environment.

    **Default**: `prod`

`PORT (Optional)`

:   The port the application will listen on.

    **Default**: `8080`

`USE_MSSQL (Optional)`

:   Whether to install the `pyodbc` package for connecting to a Microsoft SQL Server database.
    This is required if connecting to a Microsoft SQL Server database.

    **Default**: `true`

`USE_OTEL (Optional)`

:   Whether to install the `opentelemetry-instrumentation` package for tracing.

    **Default**: `false`


> Note: For information on Algorithm Configuration, see the [Reference](reference.md) section.
