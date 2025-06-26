#!/usr/bin/env python
"""
scripts/algorithm_config.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Script to manage algorithm configurations for the RecordLinker project.

The script provides the following functionalities:
    - List all algorithm configurations
        - `./scripts/algorithm_config.py list`
    - Get an algorithm configuration by its ID
        - `./scripts/algorithm_config.py get [ALGORITHM_LABEL]`
    - Add or update an algorithm
        - `./scripts/algorithm_config.py load [FILE.json]`
    - Delete an existing algorithm
        - `./scripts/algorithm_config.py delete [ALGORITHM_LABEL]`
    - Delete all algorithm configurations
        - `./scripts/algorithm_config.py clear`
"""

import argparse
import json
import sys

from sqlalchemy import orm

from recordlinker import database
from recordlinker import schemas
from recordlinker.database import algorithm_service as service
from recordlinker.models import algorithm as models

# ANSI escape codes for colors
RED = "\033[91m"
RESET = "\033[0m"


class ConfigError(Exception):
    """
    Custom exception for configuration errors.
    """

    def __init__(self, msg: str = "Configuration error"):
        self.msg = msg
        super().__init__(self.msg)


def confirm(msg: str) -> bool:
    """
    Ask the user for confirmation.
    """
    print(f"{msg} [y/N]: ", end="")
    choice = input().strip().lower()
    return choice in ["y", "yes"]


def load_json(file_path: str) -> list[dict]:
    """
    Load JSON data from a file.
    """
    with open(file_path, "rb") as fobj:
        try:
            content = json.load(fobj)
            if isinstance(content, dict):
                # if the file contains a single object, convert to list
                content = [content]
            return content
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Error loading JSON file: {exc}")


def list_configs(session: orm.Session) -> None:
    """
    List all algorithm configurations.
    """
    objs = service.list_algorithms(session)
    data = [schemas.AlgorithmSummary.model_validate(a).dict() for a in objs]
    print(json.dumps(data, indent=2), file=sys.stdout)


def get_config(label: str, session: orm.Session) -> None:
    """
    Get an algorithm configuration by its label.
    """
    obj = service.get_algorithm(session, label)
    if not obj:
        raise ConfigError(f"Algorithm '{label}' not found.")
    data = schemas.Algorithm.model_validate(obj).dict()
    print(json.dumps(data, indent=2), file=sys.stdout)


def load_config(file_path: str, session: orm.Session) -> None:
    """
    Load an algorithm configuration from a file.
    """
    msgs: list[str] = []
    for algo in load_json(file_path):
        obj = service.get_algorithm(session, algo["label"])
        if obj and not confirm(f"'{obj.label}' already exists. Do you want to replace?"):
            continue
        try:
            obj, created = service.load_algorithm(session, schemas.Algorithm(**algo), obj)
            msg = f"Created: {obj.label}" if created else f"Updated: {obj.label}"
            msgs.append(msg)
        except Exception as exc:
            raise ConfigError(f"Error loading algorithm: {exc}")
    print("\n".join(msgs), file=sys.stdout)


def delete_config(label: str, session: orm.Session) -> None:
    """
    Delete an algorithm configuration by its label.
    """
    obj: models.Algorithm | None = service.get_algorithm(session, label)
    if not obj:
        raise ConfigError(f"Algorithm '{label}' not found.")
    if confirm(f"Do you want to delete the algorithm '{label}'?"):
        service.delete_algorithm(session, obj)


def clear_configs(session: orm.Session) -> None:
    """
    Clear all algorithm configurations.
    """
    # ask the user if they want to replace or exit
    if confirm("Do you want to delete ALL Algorithms?"):
        service.clear_algorithms(session)


def main() -> None:
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(description="Manage algorithm configurations")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Subcommand: list
    subparsers.add_parser("list", help="List all algorithm configurations")

    # Subcommand: get
    get_parser = subparsers.add_parser("get", help="Get a configuration by algorithm label")
    get_parser.add_argument("algorithm_label", type=str, help="The label of the algorithm")

    # Subcommand: load
    load_parser = subparsers.add_parser(
        "load", help="Load or update an algorithm configuration from a file"
    )
    load_parser.add_argument("file_path", type=str, help="Path to the .json configuration file")

    # Subcommand: delete
    delete_parser = subparsers.add_parser(
        "delete", help="Delete an existing algorithm configuration"
    )
    delete_parser.add_argument(
        "algorithm_label", type=str, help="The label of the algorithm to delete"
    )

    # Subcommand: clear
    subparsers.add_parser("clear", help="Delete all algorithm configurations")

    args = parser.parse_args()

    session = next(database.get_session())  # Start the generator to obtain a session
    try:
        if args.command == "list":
            list_configs(session)
        elif args.command == "get":
            get_config(args.algorithm_label, session)
        elif args.command == "load":
            load_config(args.file_path, session)
        elif args.command == "delete":
            delete_config(args.algorithm_label, session)
        elif args.command == "clear":
            clear_configs(session)
        else:
            parser.print_help()
        session.commit()  # Commit the transaction if all operations succeed
    except ConfigError as exc:
        session.rollback() # Rollback the transaction if an error occurs
        print(f"{RED}{exc.msg}{RESET}", file=sys.stderr)
        raise SystemExit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
