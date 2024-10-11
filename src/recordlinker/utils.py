import copy
import importlib
import json
import pathlib
import typing


def project_root() -> pathlib.Path:
    """
    Returns the path to the project root directory.
    """
    cwd = pathlib.Path(__file__).resolve()
    root = cwd

    while not (root / "pyproject.toml").exists():
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
