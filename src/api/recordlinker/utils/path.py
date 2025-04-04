import json
import pathlib


def project_root() -> pathlib.Path:
    """
    Returns the path to the project root directory.
    """
    root = pathlib.Path(__file__).resolve()
    while root.name != "recordlinker":
        if root.parent == root:
            raise FileNotFoundError("recordlinker project root not found.")
        root = root.parent
    return root


def read_json(path: str) -> dict:
    """
    Loads a JSON file.
    """
    if not pathlib.Path(path).is_absolute():
        # if path is relative, append to the project root
        path = str(pathlib.Path(project_root(), path))
    with open(path, "r") as fobj:
        return json.load(fobj)
