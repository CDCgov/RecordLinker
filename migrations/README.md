# Migrations

## Overview

[Alembic](https://alembic.sqlalchemy.org/en/latest/) is used to manage the database schema,
due to its strong support for [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/quickstart.html).

## Synchronization

Record Linker supports 3 different models for synchronizing the database schema with an environment.
All 3 will require the `DB_URI` environment variable to be set.

### Auto-initialize

The default, and recommended approach for new environments, is to run the application server
with the `INITIALIZE_TABLES` environment variable set to **true** (this is the default). This
will automatically create all of the required database tables and stamp the migrations table with
the current revision.

**WARNING:** This process assumes you are running one instance of the Record Linker application.
If you're running multiple instances, that share a single database, you'll need to proceed with
care. As the instances may attempt to create the same set of tables simultaneously.

``sh
uvicorn recordlinker.main:app --app-dir src
```

### Manual online migrations

If you have an exisitng databse, and want to incrementally update the schema.  You can run
the following command to upgrade to the latest revision:

```sh
alembic upgrade head
```

### Manual offline migrations

If you have an exisitng databse, and want to incrementally update the schema, but are unable
to apply them directly to the database. You can run the following command to create a set of SQL
scripts that can be applied to the database:

```sh
alembic upgrade head --sql
```

**NOTE:** Be sure to set the DB_URI to the database you want to upgrade.  It doesn't need to have
access to that database, but the specific type (eg Postgres, SQL Server, etc) is required so the
appropriate SQL statements can be generated.

**NOTE:** You may need to delete some of the SQL statements generated if they've already been
applied in the environment you're upgrading.

## Create a migration

1. Update `src/recordlinker/models/*` with the changes you would like to make to the schema.
2. Run the following command:

```sh
alembic revision --autogenerate -m "<description>"
```
You can now see a new migration script in the `alembic/versions/` directory.
