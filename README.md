# Construct.py

The configuration module you never knew existed but desperately need.

This is still under development, expect some adventures!

## Table of Contents
1. [What is Construct.py?](#what_is_construct_py)
2. [Installation](#installation)
3. [Usage](#usage)
	1. [Modules](#modules)
1. [Layout of (TOML) Configuration Files](#layout)
	1. [Types](#types)
	2. [Args](#args)
	3. [Kwargs](#kwargs)
1. [Type Descriptions](#type_descriptions)
	1. [X](#x)
	2. [constant](#constant)
	3. [generic](#generic)
1. [Calling Function Defined in Your Code](#calling)
1. [Custom Types](#custom_types)

## What is Construct.py?<a name="what_is_construct_py"></a>

Construct.py is a Python package that allows you to construct **any** object
from a configuration file. For example, to construct a CNN in PyTorch with a
single convolutional layer and two dense layers, you could use:
```toml
# This file is an example configuration file on how to construct a
# convolutional neural network using PyTorch
[0]
type = "torch.nn.Sequential"

# First layer is a convolutional layer
# This shows the second method of using positional arguments. The 0th
# argument to the torch.nn.Sequential is defined here.
[0.0]
type = "torch.nn.Conv2d"
args = [4, 10, 3]  # Here is the second way of defining positional arguments

# Then we add a ReLU nonlinearity
[0.1]
type = "torch.nn.ReLU"

# We flatten the output of the convolutional layer
[0.2]
type = "torch.nn.Flatten"
args = []

# Then add a linear layer
[0.3]
type = "torch.nn.Linear"
args = ["<-constant(2)", 5]

# Don't use a bias for the linear layer
# Here is the first way of defining keyword arguments
[0.3.kwargs]
bias = false

# Then we have another ReLU nonlinearity
[0.4]
type = "torch.nn.ReLU"

# Followed by a linear layer
[0.5]
type = "torch.nn.Linear"
args = ["<-constant(5)", 1]

# And finally, use a bias on the last layer
# Here is the second way of defining keyword arguments
[0.5.bias]
type = "constant"
args = [true]
```
Note that you can use any configuration file type that can be parsed into a
`dict`. Above I've used `toml`, but nothing stops you from using a `json` or
`yaml` file.

For example configuration files, see the `examples/` directory.

## Installation <a name="installation"></a>
To install Construct.py:
```
pip install git+https://github.com/samuelfneumann/Construct-Py.git#egg=construct_py
```

## Usage <a name="usage"></a>

There is a single function that is the workhorse of Construct.py. This function
is called `parse`. To parse a configuration file, first read it into a `dict`.
For example, given a configuration file called `net.toml` in the current
working directory:
```python
from construct_py import parse
import tomli
import torch

with open("net.toml", "rb"): as infile:
	config = tomli.load(infile)

network = parse(config)
```

### Modules <a name="modules"></a>

Generally, you'll be using Construct.py to configure objects from some module.
To do that, Construct.py needs to know about these modules. Construct.py will
look in the file `.construct_py_imports.py` to find a list of modules to
import.

For example, if we wanted to
parse the above PyTorch configuration file, then we would need a
`.construct_py_imports.py` file in the current working directory to tell
Construct.py to import PyTorch:
```python
import torch
```
Actually, the imports file can be used to defined anything you want
Construct.py to know about. For example, you could define a function in that
file in which case that function is available to **call** in your
configuration file. Alternatively, you could even use:
```python
exec(open("some_file.py").read())
```
to import the contents of some Python file and evaluate it in the imports file.
By doing so, everything in `some_file.py` is available to Construct.py.

You can call any function defined in the imports file (see below) or use any
constant defined in the imports file in a configuration file.

Of course, sometimes we don't want this import file to be in the current
working directory. If you want to specify another directory to contain this
file, then you'll need to set the environment variable
`construct_PY_IMPORT_DIR` to the directory which contains the imports file. For
example, if `.construct_py_imports.py` is located at
`~/some/other/directory/.construct_py_imports.py`, then you'll need to set and
export `construct_PY_IMPORT_DIR=~/some/other/directory`. For example, you could
add the following to your `.zshrc`:
```zsh
export construct_PY_IMPORT_DIR=~/some/other/directory
```

## Layout of (TOML) Configuration Files <a name="layout"></a>

Each configuration file is treated as a *Call Tree*, which denotes function
calls with their arguments. The tree should have a single root node, which
determines which object is created. This is the first layer `[0]` in the
configuration file above, and results in the creation of a
`torch.nn.Sequential`. In effect, the root node is a node to create a
`torch.nn.Sequential`.

Each object in the hierarchy is defined by a sequence of numbers such as
`0.1.2.3.4`. These numbers refer to positional arguments to function calls.
For example,
above the configuration of `[0.0]` refers to the first argument to the
configuration of `[0]`. Similarly, `[0.x]` refers to the `xth` argument to the
function call defined in `[0]`. Each `.` refers to a new depth of the tree. For
example, `[0.x.y.z]` is the `zth` argument to the `yth` function call, which
itself is the `xth` argument to the final constructed object, defined in layer
`[0]`. If instead of number, you used string, then these are treated as keyword
arguments. For example `[0.kwarg]` would be a keyword argument with name
`kwarg` to the call of the function defined in `[0]`.

Each successive configuration layer has the following form:

```toml
[x]
type = t # some type description
args = l # a list of values
[x.kwargs]
# key = value pairs
```

where `x` can be any sequence of numbers separated by a `.`, `t` is some type
description (described below), and `l` is a list of values.

### `type` <a name="types"></a>

Each successive layer has a `type`, which defines which function is called or
what object is created. Valid `type` values are:

Type Value   |   Interpretation
-------------|------------------
`X` 		 | Call the function `X` in the code. `X` can be any valid callable symbol which is defined in the code, but must be **fully qualified**.
`generic`    | Call any generic Python code such as `lambda x: x + 1`
`constant`   | Return a constant

Custom `type`s can be registered using the `register` function. More on that
later. See below on what each of these types mean.

### `args` <a name="args"></a>

Each configuration layer also has an associated `args` key. The value of this
must be a `list`. In this list, you can put any valid constant value such as
`args=[1, 2, 3, "hello", 1.2, false]`. If you use a string, prepending a `:` to
the string will cause the string to be evaluated at runtime. For example, given
the following function in your code:
```python
def f(x):
	return x + 1
```
then if you specify `args=[1, 2, ":f(2)"]` in your code, this will be expanded
to `args=[1, 2, 3]` at runtime. Of course, Construct.py needs to know about the
function `f`, and so it would need to be defined in the imports file.

There is an alternative method to specifying arguments. Instead of having a
list of constants, you could have a tree-like objecture. For an argument to the
function call at layer `[i]`, you can specify the positional arguments as
[i.j]` for each positional argument `j`. The positional arguments have to be
enumerated starting from 0 and have an increment of 1. The benefit of this
second approach is it allows the positional arguments themselves to be
complicated objects which are themselves constructed by a portion of the
configuration file. For example, the top-level object at position `[0]` could
be a `torch.nn.Sequential`, and one of its children could also be a
`torch.nn.Sequential`. This functionality is not available with the first
positional argument method, which allows only simple objects to be
constructed as positional arguments.

The two different methods of using positional arguments are mutually exclusive.
You cannot use both.

### `kwargs` <a name="kwargs"></a>

Keyword arguments for layer `[0...x]` are placed in a dictionary at
`[0...x.kwargs]` where the `...` refers to any number of nested
sub-configurations. For example, the keyword arguments for layer `[0.x.y]` are
placed at `[0.x.y.kwargs]`. Each keyword argument is simply listed as a
key-value pairs:
```toml
[0.x.y.kwargs]
"key1" = "value1"
"key2" = "value2"
#...
```

Like positional arguments, there is an alternative way of specifying keyword
arguments. Instead of specifying a bunch of key-value pairs at [0.x.y.kwargs]`,
you could instead specify the keyword arguments by name. For example, for a
keyword argument named `this_is_a_kwarg_name`, you could specify
`[0.x.y.this_is_a_kwarg_name]`. Then, the configuration sub-tree below this
level can be a configuration of some complex object, similar to how the second
method of specifying positional arguments works.

The two methods of using keyword arguments are mixable.

## `type`s <a name="type_descriptions"></a>

### `X` <a name="x"></a>

The syntax `X` allows us to create an object or run a function with the symbol
`X`. To this function, we can pass in any arguments using the `args` key, or we
can create a subtree below this node, where each path in the subtree will
denote a sequential argument. If the `X` node is at position `1.x` in the
tree, then the `yth` argument to `X` will be at position `1.x.y`. Hence, we
have an ordering of arguments. The benefit to this approach is that any
argument to the function can be a subtree of many, many elements, and so it's
easy to construct complex objects or call functions on complex objects.

For example, if we want to create object `A`, but object `A` takes in object
`B`, which takes in object `C`, we can easily do the following:
```TOML
[0]
type = "A"

[0.0]
type = "B"

[0.0.0]
type = "C"

[0.0.0.y]
# Arguments to create C, where y = 0, 1, 2, ...

[0.0.x]
# Other arguments to create B, where x = 1, 2, 3, ...

[0.z]
# Other arguments to create A, where z = 1, 2, 3, ...
```
This effectively creates an object by calling `A(B(C(...), ...), ...)`.

One caveat to using `X` is that names must be **fully qualified** based on the
imports file. So, if you have the following module tree:
```
module X
	module Y
		function y
```
and you have the following in your imports file:
```python
import X
```
then to use `y` in a configuration file you need to specify it as `X.Y.y`. In
instead you import `Y` in your imports file, you can specify `y` as `Y.y`. If
you use `from X.Y import y` in your imports file, then you can specify `y` as
`y` in your configuration file. The general rule is that however you would
access the symbol `y` in your imports file, that's how `y` must be specified
in your configuration file as well. This goes for all `type`s, not just the `X`
type.

### `constant`<a name="constant"></a>

With the `constant` type, we can return any constant value, defined by the
**single** value in the `args` array. For example:
```toml
[0]
type = "constant"
args = [1]
```
is a configuration file which, when parsed, results in a `1`.

### `generic` <a name="generic"></a>

With the `generic` type, we can call any arbitrary Python code by passing the
code as a single argument in `args`. `generic` takes only a single argument. To
use a `generic` type in your configuration file, you could do something like
this:
```toml
[0]
type = "generic"
args = ["lambda x: x + 1"]
```
this would construct a function that adds `1` to its argument.

## Calling Functions or Creating Objects Defined in the Code <a name="calling"></a>

One awesome feature is that if a function or object is defined in your Python
code, then that code can be called from the configuration file as long as that
code is available in your imports file!
Well, not exactly, but almost! Really, the configuration is deferred to
runtime, so when we create an object, we can just run some functions and put
the returned values in the call tree.

For example, if you have a function `f` defined in your
imports with a variable `x` defined in your imports file,
then you can call `f(x)` in your configuration file by using the `<-f(x)`
operator.

Two functions come bundled with Construct.py that can be called without
defining them in the imports file. These are `constant` and `generic` as
defined above. Hence, from any configuration file you can use `<-constant(x)`
or `<-generic(x)` by default. For example:
```toml
[0]
type = "torch.nn.Linear"
args = ["<-generic(1)", "<-constant(3)", true]
```
creates a `torch.nn.Linear` with 1 input, 3 outputs, and a bias unit.

## Custom `type`s <a name="custom_types"></a>

Custom types can be implemented in two ways. First, you can just make a custom
object and then use a configuration file to create it. Second, you can register
a function to be called with a specific type using the `register` method. For
example, calling `Construct.register(type, f)` will cause `f` to be called with
`args` and `kwargs` whenever `type` is encountered in a configuration file. For
example if `register("agent", make_agent)` is called in your code then whenever
a configuration file has something like:
```toml
[1.x]
type = "agent"
args = [...]
[1.x.kwargs]
...
```
then `make_agent(args..., kwargs...)` will be called when parsing the
configuration file.

## ToDo

- [ ] Docstrings
