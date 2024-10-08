#!/usr/bin/env python
"""
scripts/algorithm_config.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script allows users to manage the algorithm configurations for the
RecordLinker project.

The script provides the following functionalities:
    - List all algorithm configurations
        - `./scripts/algorithm_config.py list`
    - Get an algorithm configuration by its ID
        - `./scripts/algorithm_config.py get [ALGORITHM_LABEL]`
    - Add or update an algorithm
        - `./scripts/algorithm_config.py load [FILE.YML]`
    - Delete an existing algorithm
        - `./scripts/algorithm_config.py delete [ALGORITHM_LABEL]`
    - Delete all algorithm configurations
        - `./scripts/algorithm_config.py clear`
"""

import argparse
import sys

import yaml
from sqlalchemy import orm

from recordlinker import database
from recordlinker import schemas
from recordlinker.linking import algorithm_service as service

# ANSI escape codes for colors
RED = "\033[91m"
RESET = "\033[0m"


def error(msg: str) -> None:
    """
    Print an error message in red text.
    """
    print(f"{RED}{msg}{RESET}", file=sys.stderr)


def list_configs(session: orm.Session) -> None:
    """
    List all algorithm configurations.
    """
    objs = service.list_algorithms(session)
    data = [schemas.Algorithm.model_validate(obj) for obj in objs]
    content = [d.model_dump(include=["label", "description"]) for d in data]
    print(yaml.dump(content, default_flow_style=False), file=sys.stdout)


def get_config(session: orm.Session, label: str) -> None:
    """
    Get an algorithm configuration by its label.
    """
    try:
        obj = service.get_algorithm(session, label)
    except Exception as exc:
        error(f"Error retrieving algorithm: {exc}")
        sys.exit(1)
    if obj:
        data = schemas.Algorithm.model_validate(obj)
        content = {"algorithm": [data.model_dump()]}
        print(yaml.dump(content, default_flow_style=False), file=sys.stdout)
    else:
        error(f"Algorithm with label '{label}' does not exist.")
        sys.exit(1)


def load_config(session: orm.Session, file_path: str) -> None:
    """
    Load an algorithm configuration from a file.
    """
    with open(file_path, "rb") as fobj:
        # load data from yaml file
        try:
            content = yaml.safe_load(fobj)
        except yaml.YAMLError as exc:
            error(f"Error loading YAML file: {exc}")
            sys.exit(1)

        loaded: dict[str, list] = {"added": [], "updated": []}
        for algo in content.get("algorithm", []):
            try:
                data = schemas.Algorithm(**algo)
                obj = service.get_algorithm(session, data.label)
                if obj:
                    # ask the user if they want to replace or exit
                    print(f"Algorithm with label '{obj.label}' already exists.")
                    print("Do you want to replace it? [y/N]: ", end="")
                    choice = input().strip().lower()
                    if choice not in ["y", "yes"]:
                        sys.exit(0)
                obj, created = service.load_algorithm(session, data, obj, commit=False)
                key = "added" if created else "updated"
                loaded[key].append(obj.label)
            except (ValueError, TypeError, AssertionError) as exc:
                error(f"Error parsing algorithm: {exc}")
                sys.exit(1)
        try:
            SESSION.commit()
        except Exception as exc:
            error(f"Error committing to the database: {exc}")
            sys.exit(1)
        print(f"Added: {loaded['added']}", file=sys.stdout)
        print(f"Updated: {loaded['updated']}", file=sys.stdout)


def delete_config(session: orm.Session, label: str) -> None:
    """
    Delete an algorithm configuration by its label.
    """
    obj = service.get_algorithm(session, label)
    if obj:
        print(f"Do you want to delete Algorithm {label}? [y/N]: ", end="")
        choice = input().strip().lower()
        if choice not in ["y", "yes"]:
            sys.exit(0)
        service.delete_algorithm(session, obj, commit=True)
    else:
        error(f"Algorithm with label '{label}' does not exist.")
        sys.exit(1)


def clear_configs(session: orm.Session) -> None:
    """
    Clear all algorithm configurations.
    """
    # ask the user if they want to replace or exit
    print("Do you want to delete ALL Algorithms? [y/N]: ", end="")
    choice = input().strip().lower()
    if choice not in ["y", "yes"]:
        sys.exit(0)
    service.delete_all_algorithms(session, commit=True)


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
    load_parser.add_argument("file_path", type=str, help="Path to the .yml configuration file")

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

    session_maker = database.get_sessionmaker()
    with session_maker.context_session() as session:
        if args.command == "list":
            list_configs(session)
        elif args.command == "get":
            get_config(session, args.algorithm_label)
        elif args.command == "load":
            load_config(session, args.file_path)
        elif args.command == "delete":
            delete_config(session, args.algorithm_label)
        elif args.command == "clear":
            clear_configs(session)
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
