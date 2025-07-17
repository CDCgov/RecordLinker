# Application Configuration


## Application Settings

The Record Linker application is configured via a
[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
configuration class. The settings are loaded from environment variables or a `.env` file,
allowing for easy customization without modifying the code.  When both an environment 
variable and a `.env` file are present, the environment variable takes precedence.
> 💡 For information on algorithm configuration, see the [Algorithm Configuration](algo-configuration.md) section.

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

`INITIALIZE_TABLES (Optional)`

:   Whether to initialize the database tables on startup if the database is empty.

    **Docker Default**: `true`

    **Development Default**: `true`

`INITIAL_ALGORITHMS (Optional)`

:   Path to a JSON file with initial algorithms to load if the algorithms table is empty.

    **Docker Default**: `assets/initial_algorithms.json`

    **Development Default**: `assets/initial_algorithms.json`

`API_ROOT_PATH (Optional)`

:   Root path from which the Record Linker API will be exposed.

    **Docker Default**: `/api`

    **Development Default**: `/api`

`TUNING_ENABLED (Optional)`

:   Whether to enable the tuning API endpoints.

    **Docker Default**: `false`

    **Development Default**: `false`

`TUNING_TRUE_MATCH_PAIRS (Optional)`

:   Number of true match pairs to use for tuning.

    **Docker Default**: `10000`

    **Development Default**: `10000`

`TUNING_NON_MATCH_PAIRS (Optional)`

:   Number of non match pairs to use for tuning.

    **Docker Default**: `100000`

    **Development Default**: `100000`

`TUNING_NON_MATCH_SAMPLE (Optional)`

:   Number of patient records to sample from when selecting non match pairs.

    **Docker Default**: `250000`

    **Development Default**: `250000`

`TUNING_JOB_TIMEOUT (Optional)`

:   Number of seconds to wait for a tuning job to finish before canceling it.

    **Docker Default**: `3600`

    **Development Default**: `3600`


## Database Options

The `DB_URI` and `TEST_DB_URI` settings can be configured to connect to a compatible
[SQLAlchemy](https://www.sqlalchemy.org/) database.  By default, the following database
drivers are installed allowing for connections to:

- **[sqlite3](https://docs.python.org/3/library/sqlite3.html) (sqlite)**

    Example: `sqlite:///db.sqlite3`

- **[psycopg2](https://www.psycopg.org/) (postgresql)**

    Example: `postgresql+psycopg2://user:password@localhost/dbname`

- **[pymysql](https://pymysql.readthedocs.io/en/latest/) (mysql / mariadb)**

    Example: `mysql+pymysql://user:password@localhost/dbname`

- **[pyodbc](https://github.com/mkleehammer/pyodbc/wiki) (sql server)**

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
