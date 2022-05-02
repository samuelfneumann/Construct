import os

# Any modules you need to construct objects from should be placed in an imports
# file
_PREFIX = os.environ.get("CONSTRUCT_PY_IMPORTS_DIR", ".")
_CONFIG_FILE = f"{_PREFIX}/.construct_py_imports.py"
if os.path.exists(_CONFIG_FILE):
    print(f"imorting from {_CONFIG_FILE}")
    exec(open(_CONFIG_FILE).read())

# Alternatively, you can import the main module, in which case the program will
# "just work". Two caveats to this approach:
#   1) This can very easily turn your program into a pretzel
#   2) In the configuration files, modules need to be prefixed with __main__
# import __main__


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
