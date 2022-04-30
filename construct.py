import torch
import tomli


class _Construct:
    def __init__(self):
        self._custom_ops = {}

    def _register(self, type_: str, f):
        self._custom_ops[type_] = f

    def _construct(self, type_: str):
        if type_ not in self._custom_ops:
            return eval(type_)
        return self._custom_ops[type_]

        # return self._custom_ops.get(type_, eval(type_))


_construct = _Construct()


def construct(type_: str):
    return _construct._construct(type_)


def register(type_: str, f):
    _construct._register(type_, f)


# Register some custom functions
register("constant", lambda x: x)
register("generic", lambda x: eval(x))


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
        # print("key", key, config)
        return _parse(config[key], False)

    # Get positions of positional arguments
    args = []
    keys = sorted(keys)
    int_keys = filter(lambda x: x.isdecimal(), keys)

    # Construct positional arguments
    for k in int_keys:
        args.append(_parse(config[k], False))

    # Ensure only one form of positional argument was given
    if "args" in config.keys() and args:
        raise ValueError("args can only be specified in one form")
    elif len(args) == 0 and "args" in config.keys():
        args = config["args"]

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
                kwargs[k] = config["kwargs"][k]

    # Construct the object
    constructor = construct(config["type"])
    return constructor(*args, **kwargs)


with open("net.toml", "rb") as i:
    d = tomli.load(i)

# print(d)
# out = construct(d["1"]["type"], d["1"]["args"], d["1"]["kwargs"])
print("out", _parse(d))
