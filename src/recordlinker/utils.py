import copy
import importlib
import inspect
import json
import pathlib
import typing


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
    if val.startswith("fn:"):
        val = val[3:]
    try:
        # Split the string into module path and function name
        module_path, func_name = val.rsplit(".", 1)
        # Import the module
        module = importlib.import_module(module_path)
        # Get the function from the module
        return getattr(module, func_name)
    except Exception as e:
        raise ValueError(f"Failed to convert string to callable: {val}") from e


def func_to_str(func: typing.Callable) -> str:
    """
    Converts a function to a string representation of the function.
    """
    return f"func:{func.__module__}.{func.__name__}"


def check_signature(fn: typing.Callable, expected: typing.Callable) -> bool:
    """
    Validates if the callable `fn` matches the signature defined by `expected`.

    Parameters:
    - fn: The function to validate.
    - expected: The expected signature as a typing.Callable.

    Returns:
    - bool: True if signatures match, False otherwise.
    """

    # Helper function to compare types considering generics
    def _compare_types(actual_type, expected_type):
        actual_origin = typing.get_origin(actual_type) or actual_type
        expected_origin = typing.get_origin(expected_type) or expected_type

        if not isinstance(actual_origin, type):
            actual_origin = type(actual_origin)

        if actual_origin != expected_origin:
            return False

        actual_args = typing.get_args(actual_type)
        expected_args = typing.get_args(expected_type)
        return actual_args == expected_args

    # Extract the expected argument and return types from the `typing.Callable`
    expected_args, expected_return = expected.__args__[:-1], expected.__args__[-1]  # type: ignore

    # Get the function signature of `fn`
    try:
        fn_signature = inspect.signature(fn)
    except (TypeError, ValueError):
        return False  # Not a callable

    # Extract parameter types from the actual callable
    fn_params = list(fn_signature.parameters.values())
    if len(fn_params) != len(expected_args):
        return False  # Argument count mismatch

    # Compare each argument type
    for fn_param, expected_param_type in zip(fn_params, expected_args):
        if not _compare_types(fn_param.annotation, expected_param_type):
            return False  # Argument type mismatch

    # Compare return type
    return _compare_types(fn_signature.return_annotation, expected_return)


class MockTracer:
    """
    A no-op OTel tracer that can be used in place of a real tracer. This is useful
    for situations where users decide to not install the otelemetry package.
    """
    def start_as_current_span(self, name, **kwargs):
        """Returns a no-op span"""
        return self

    def __enter__(self):
        """No-op for context manager entry"""
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        """No-op for context manager exit"""
        pass

    def start_span(self, name, **kwargs):
        """Returns a no-op span"""
        return self
