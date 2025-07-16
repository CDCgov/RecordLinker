import json
import os.path
import pathlib


def code_root() -> pathlib.Path:
    """
    Returns the root directory of the recordlinker source code.
    """
    root = pathlib.Path(__file__).resolve()
    while root.name != "recordlinker":
        if root.parent == root:
            raise FileNotFoundError("recordlinker project root not found.")
        root = root.parent
    return root


def repo_root(start: pathlib.Path | None = None) -> pathlib.Path | None:
    """
    Returns the root directory of the recordlinker repository, or None if not found.
    """
    start = start or pathlib.Path(__file__).resolve()
    for directory in [start] + list(start.parents):
        if (directory / "pyproject.toml").is_file():
            return directory
    return None


def rel_path(path: pathlib.Path) -> str:
    """
    Return a path relative to the CWD of the given path.
    """
    cwd: pathlib.Path = pathlib.Path.cwd()
    return str(os.path.relpath(path, cwd))


def read_json(path: str) -> dict:
    """
    Loads a JSON file.
    """
    if not pathlib.Path(path).is_absolute():
        # if path is relative, append to the project root
        path = str(pathlib.Path(code_root(), path))
    with open(path, "r") as fobj:
        return json.load(fobj)
