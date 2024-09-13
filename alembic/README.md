# Migrations

## Overview

To manage Master Patient Index (MPI) database migrations, we use [Alembic](https://alembic.sqlalchemy.org/en/latest/) due to its strong support for [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/quickstart.html) and all the [databases](https://docs.sqlalchemy.org/en/20/dialects/) it supports.

## How to Run a Migration

### Update MPI Schema
**Step 1:** Update `src/recordlinker/linkage/models.py` with the changes you would like to make to the MPI schema.

### Create a Migration Script
**Step 2:** In the CLI, navigate to the `alembic/` directory and use the following command to run a revision:
```bash
alembic revision -m "<description>"
```
You can now see a new migration script in the `alembic/versions/` directory.

### Run the Migration
**Step 3:** Finally, use the following command to run the migration:
```bash
alembic upgrade head
```