import json
import pathlib


def project_root() -> pathlib.Path:
    """
    Returns the path to the project root directory.
    """
    cwd = pathlib.Path(__file__).resolve()
    root = cwd

    # FIXME: this only works when in the git project root and will fail if we install the
    # package into the site-packages
    while not (root / "pyproject.toml").exists():
        if root.parent == root:
            raise FileNotFoundError("Project root with 'pyproject.toml' not found.")
        root = root.parent
    return root


def read_json(*filepaths: str) -> dict:
    """
    Loads a JSON file.
    """
    filename = pathlib.Path(project_root(), *filepaths)
    with open(filename, "r") as fobj:
        return json.load(fobj)
