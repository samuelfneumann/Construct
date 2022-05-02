import sys
from sys import stderr
import os

# Any modules you need to construct objects from should be placed in an
# imports file
_PREFIX = os.environ.get("CONSTRUCT_PY_DIR", ".")
_INCLUDES_FILE = f"{_PREFIX}/construct_py_includes.py"
if os.path.exists(_INCLUDES_FILE):
    print(f"Construct.py: using includes file {_INCLUDES_FILE}", file=stderr)
    exec(open(_INCLUDES_FILE).read())

_IMPORTS_FILE = f"{_PREFIX}/construct_py_imports.py"
if os.path.exists(_IMPORTS_FILE):
    sys.path.append(_IMPORTS_FILE)
    print(f"Construct.py: using imports file {_IMPORTS_FILE}",
          file=stderr)
    from construct_py_imports import *

# Import the main module?
_USE_MAIN = os.environ.get("CONSTRUCT_PY_USE_MAIN", "") != ""
if _USE_MAIN:
    # Alternatively, you can import the main module, in which case the
    # program will "just work". Two caveats to this approach:
    # 1) This can very easily turn your program into a pretzel
    # 2) In the configuration files, modules need to be prefixed with __main__
    import __main__


class _Custom:
    def __init__(self):
        self._custom_ops = {}

    def _register(self, type_: str, f):
        self._custom_ops[type_] = f

    def _custom(self, type_: str):
        if type_ not in self._custom_ops:
            return eval(type_)
        return self._custom_ops[type_]

        # return self._custom_ops.get(type_, eval(type_))


_custom = _Custom()


def _construct(type_: str):
    return _custom._custom(type_)


def register(type_: str, f):
    _custom._register(type_, f)


def constant(x):
    return x


def generic(x):
    return _eval(x)


# Register some custom functions
register("constant", constant)
register("generic", generic)


def parse(config: dict):
    return _parse(config, True)


def _parse(config: dict, top_level: bool = True):
    keys = list(config.keys())

    if "type" in keys:
        keys.remove("type")
    if "args" in keys:
        keys.remove("args")
    if "kwargs" in keys:
        keys.remove("kwargs")

    if len(keys) == 1 and '0' in keys and top_level:
        # Top-level of configuration dict
        key = keys[0]

        if not isinstance(config[key], dict):
            raise ValueError(f"expected a dict but got {type(config[key])}")
        return _parse(config[key], False)

    # Get positions of positional arguments
    args = []
    keys = sorted(keys)
    int_keys = list(filter(lambda x: x.isdecimal(), keys))

    # Construct positional arguments
    for k in int_keys:
        args.append(_parse(config[k], False))

    # Ensure only one form of positional argument was given
    if "args" in config.keys() and args:
        raise ValueError("args can only be specified in one form")
    elif len(args) == 0 and "args" in config.keys():
        args = list(map(lambda x: _eval(x), config["args"]))

    # Construct all kwargs
    kwargs = {}
    str_keys = filter(lambda x: not x.isdecimal(), keys)
    for k in str_keys:
        kwargs[k] = _parse(config[k], False)

    # Combine both methods of kwargs
    if "kwargs" in config.keys():
        for k in config["kwargs"]:
            if k in kwargs:
                raise KeyError(f"cannot have duplicate key {k})")
            else:
                kwargs[k] = _eval(config["kwargs"][k])

    # Construct the object
    constructor = _construct(config["type"])
    return constructor(*args, **kwargs)


def _eval(expr):
    if isinstance(expr, str) and len(expr) > 2 and expr.startswith("<-"):
        return eval(expr[2:])
    return expr


def set_at(config: dict, value, *positions):
    """
    Set the argument in the call tree at position `*positions` to value.

    The index for the top level object needs never be specified. That is, if
    any index is specified, it is taken to index the arguments to the top level
    object, not the single top level object itself.

    Each consecutive value in `positions` refers to either an argument or
    keyword argument. If the value is an int, then it is taken to refer to a
    positional argument. If it is a string, then the value is taken to refer to
    a keyword argument. For example, if `positions = (0, "y", 3)`, then
    calling `set_at` with this `positions` would change the value of the third
    argument to the keyword argument `y` of the first argument of the
    top-level object. `positions` is just a simple indexing mechanism, similar
    to how lists and dicts are indexed.

    Parameters
    ----------
    config : dict
        The configuration dictionary to modify before parsing
    value : any
        The value to set
    *positions : int or str
        The position of the argument to set to `value`

    Returns
    -------
    dict
        The modified configuration dictionary

    Examples
    --------
    ```python
    >>> config = {
            '0': {
                'type': 'env.mountain_car.MountainCar',
                'args': ["SEED", 0.99],
                'kwargs': {
                    'continuous_action': False,
                },
            },
        }
    >>> set_at(config, 1, 0)
    >>> set_at(config, True, "continuous_action")
    >>> config
        {
            '0': {
                'type': 'env.mountain_car.MountainCar',
                'args': [1, 0.99],
                'kwargs': {
                    'continuous_action': True,
                },
            },
        }
    >>> set_at(config, "what did I just do?")
    >>> config
    {'0': "what did I just do?"}
    ```
    """
    return _set_at(config, value, [0] + positions)


def _set_at(config: dict, value, *positions):
    if len(positions) == 0:
        config[0] = value

    if isinstance(positions, tuple):
        position = positions[0]
    else:
        position = positions

    if len(positions) == 1:
        config[position] = value
        return config

    if isinstance(position, int):
        position = str(position)

    if isinstance(positions[1], int):
        set(config[position]["args"], value, *positions[1:])
    else:
        set(config[position]["kwargs"], value, *positions[1:])
