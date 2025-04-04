import copy
import importlib
import typing


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
