import copy
import importlib
import json
import logging
import pathlib
import subprocess
import typing

from sqlalchemy import text
from sqlalchemy.engine import url

from recordlinker.config import settings
from recordlinker.linkage.dal import DataAccessLayer
from recordlinker.linkage.mpi import DIBBsMPIConnectorClient


def project_root() -> pathlib.Path:
    """
    Returns the path to the project root directory.
    """
    cwd = pathlib.Path(__file__).resolve()
    root = cwd

    while not (root / 'pyproject.toml').exists():
        if root.parent == root:
            raise FileNotFoundError("Project root with 'pyproject.toml' not found.")
        root = root.parent
    return root


def read_json_from_assets(*filepaths: str) -> dict:
    """
    Loads a JSON file from the 'assets' directory.
    """
    filename = pathlib.Path(project_root(), "assets", *filepaths)
    return json.load(open(filename))


def run_pyway(
    pyway_command: typing.Literal["info", "validate", "migrate", "import"],
) -> subprocess.CompletedProcess:
    """
    Helper function to run the pyway CLI from Python.

    :param pyway_command: The specific pyway command to run.
    :return: A subprocess.CompletedProcess object containing the results of the pyway
        command.
    """

    logger = logging.getLogger(__name__)

    # Extract the database type and its parts from the MPI database URI.
    db_parts = url.make_url(settings.db_uri)
    db_type = db_parts.drivername.split("+")[0]
    if db_type == "postgresql":
        db_type = "postgres"

    # Prepare the pyway command.
    migrations_dir = str(project_root() / "migrations")
    pyway_args = [
        "--database-table public.pyway",
        f"--database-migration-dir {migrations_dir}",
        f"--database-type {db_type}",
        f"--database-host {db_parts.host}",
        f"--database-port {db_parts.port}",
        f"--database-name {db_parts.database}",
        f"--database-username {db_parts.username}",
        f"--database-password {db_parts.password}",
    ]

    full_command = ["pyway", pyway_command] + pyway_args
    full_command = " ".join(full_command)

    # Attempt to run the pyway command.
    try:
        pyway_response = subprocess.run(
            full_command, shell=True, check=True, capture_output=True
        )
    except subprocess.CalledProcessError as error:
        error_message = error.output.decode("utf-8")

        # Pyway validate returns an error if no migrations have been applied yet.
        # This is expected behavior, so we can ignore this error and continue onto
        # the migrations with pyway migrate. We'll encounter this error when we
        # first deploy the service with a fresh database.
        if (
            "ERROR: no migrations applied yet, no validation necessary."
            in error_message
        ):
            logger.warning(error_message)
            return subprocess.CompletedProcess(
                args=full_command,
                returncode=0,
                stdout=None,
                stderr=error_message,
            )
        else:
            logger.error(error_message)
            raise error

    logger.info(pyway_response.stdout.decode("utf-8"))

    return pyway_response


def run_migrations():
    """
    Use the pyway CLI to ensure that the MPI database is up to date with the latest
    migrations.
    """
    logger = logging.getLogger(__name__)
    logger.info("Validating MPI database schema...")
    validation_response = run_pyway("validate")

    if validation_response.returncode == 0:
        logger.info("MPI database schema validations successful.")

        logger.info("Migrating MPI database...")
        migrations_response = run_pyway("migrate")

        if migrations_response.returncode == 0:
            logger.info("MPI database migrations successful.")
        else:
            logger.error("MPI database migrations failed.")
            raise Exception(migrations_response.stderr.decode("utf-8"))

    else:
        logger.error("MPI database schema validations failed.")
        raise Exception(validation_response.stderr.decode("utf-8"))


def _clean_up(dal: DataAccessLayer | None = None) -> None:
    """
    Utility function for testing purposes that makes tests idempotent by cleaning up
    database state after each test run.

    :param dal: Optionally, a DataAccessLayer currently connected to an instantiated
      MPI database. If not provided, the default DIBBsMPIConnectorClient is used
      to perform cleanup operations.
    """
    if dal is None:
        dal = DIBBsMPIConnectorClient().dal
    with dal.engine.connect() as pg_connection:
        pg_connection.execute(text("""DROP TABLE IF EXISTS external_person CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS external_source CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS address CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS phone_number CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS identifier CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS give_name CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS given_name CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS name CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS patient CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS person CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS public.pyway CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS algorithm_pass CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS algorithm CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS mpi_blocking_value CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS mpi_patient CASCADE;"""))
        pg_connection.execute(text("""DROP TABLE IF EXISTS mpi_person CASCADE;"""))
        pg_connection.commit()
        pg_connection.close()


def bind_functions(data: dict) -> dict:
    """
    Binds the functions in the data to the functions in the module.
    """

    def _eval_non_list(data):
        if isinstance(data, dict):
            return bind_functions(data)
        elif isinstance(data, str) and data.startswith("func:"):
            return str_to_callable(data)
        return data

    bound = copy.copy(data)
    for key, value in bound.items():
        if isinstance(value, list):
            bound[key] = [_eval_non_list(item) for item in value]
        else:
            bound[key] = _eval_non_list(value)
    return bound


def str_to_callable(val: str) -> typing.Callable:
    """
    Converts a string representation of a function to the function itself.
    """
    # Remove the "func:" prefix
    if val.startswith("func:"):
        val = val[5:]
    # Split the string into module path and function name
    module_path, func_name = val.rsplit(".", 1)
    # Import the module
    module = importlib.import_module(module_path)
    # Get the function from the module
    return getattr(module, func_name)


def func_to_str(func: typing.Callable) -> str:
    """
    Converts a function to a string representation of the function.
    """
    return f"func:{func.__module__}.{func.__name__}"
