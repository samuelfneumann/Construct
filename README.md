# Construct.py

The configuration module you never knew existed but desperately need.
**Dynamically** configure objects with **static** configuration files!

This is still under development, expect some adventures!

## Table of Contents
1. [What is Construct.py?](#what_is_construct_py)
2. [Installation](#installation)
3. [Usage](#usage)
	1. [Modules](#modules)
4. [Layout of (TOML) Configuration Files](#layout)
	1. [Types](#types)
	2. [Args](#args)
	3. [Kwargs](#kwargs)
5. [Type Descriptions](#type_descriptions)
	1. [X](#x)
	2. [constant](#constant)
	3. [generic](#generic)
	4. [side_effect](#side_effect)
	5. [arg_at/kwarg_at](#arg_at/kwarg_at)
6. [Calling Function Defined in Your Code](#calling)
7. [Custom Types](#custom_types)
8. [\_\_main\_\_](#__main__)

## What is Construct.py?<a name="what_is_construct_py"></a>

Construct.py is a Python package that allows you to construct **any** object
from a configuration file. For example, to construct a CNN in PyTorch with a
single convolutional layer and two dense layers, you could use:
```toml
# This file is an example configuration file on how to construct a
# convolutional neural network using PyTorch. In this file, a lot of features
# of Construct.py are shown. I don't recommend mixing so many features, but I
# have added them here as an example.
[0]
type = "torch.nn.Sequential"  # Notice the fully qualified name

# First layer is a convolutional layer
[0.0]
type = "torch.nn.Conv2d"
args = [1, 10, 3]

# Then we add a ReLU nonlinearity
[0.1]
type = "torch.nn.ReLU"

# We flatten the output of the convolutional layer
# Use a generic type to construct a torch.nn.Flatten. This is not recommended,
# but is here to showcase the functionality of the generic type.
[0.2]
type = "generic"
args = ["<-torch.nn.Flatten()"]

# Then add a linear layer
[0.3]
type = "torch.nn.Linear"
args = ["<-constant(2)", 5]

# Don't use a bias for the linear layer
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
[0.5.bias]
type = "constant"
args = [true]

```
Note that you can use any configuration file type that can be parsed into a
`dict`. Above I've used `toml`, but nothing stops you from using a `json` or
`yaml` file.

For example configuration files, see the `examples/` directory.

The great thing about Construct.py is that it allows you to **dynamically**
create objects from **static** configuration files. What do I mean by this? Let
me give an example:

In my research in reinforcement learning, we deal with neural networks to
approximate value functions. If that doesn't make sense, then just consider a
mathematical function `f` that takes in some number of inputs `(x, y, ...)`. In
my research, the number of inputs changes based on which environment my
experiment is run on. For example, if I run an experiment on the MountainCar
game, then there are 2 inputs to `f` (the neural network). If I run on the
CartPole game, there are inputs to `f`. Construct.py allows me to write a
**single** configuration file for a neural network such that, when I run my
experiment on MountainCar, the configuration file generates a neural network
that expects 2 inputs. I can use the **exact same** configuration file to run
an experiment on CartPole, and the configuration file will create a neural
network that expects 4 inputs. Everything else will remain the same, but the
number of inputs will change based on the environment I run on.

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
look in two different files to qualify names:
1. The *includes* file `construct_py_includes.py`
2. The *imports* file `construct_py_imports.py`

The difference between these two files is the following:
1. The source code of the `construct_py_includes.py` file is embedded in the
   source code of Construct.py above all the logic of Construct.py. The
   contents of `construct_py_includes.py` is run before Construct.py is
   interpreted upon importing Construct.py into your own module. Names defined
   in this file do not need to be fully qualified, but imported names do need
   to be fully qualified.
2. The contents of `construct_py_imports` is **imported** into Construct.py
   before Construct.py is interpreted upong importing Construct.py into your
   own module. That is, `from construct_py_imports import *` is run in
   Construct.py before any actual code of Construct.py is run. Hence, names
   defined in this file does not need to be fully qualified.

For example, if we wanted to
parse the above PyTorch configuration file, then we would need a
`construct_py_includes.py` file in the current working directory to tell
Construct.py to import PyTorch:
```python
import torch
```
This would **not** work if we used `import torch` in the imports file. This is
because what would happen is the imports file would import torch, then
Construct.py would import the imports file. Construct.py would **not** import
torch. Construct.py runs the actual source code of the
includes file (it does not import the includes file), and so Construct.py would
import torch when `import torch` is placed in the includes file. Hence if you
ever need to construct an object from another module, the `import` statement
**must** be in the includes file.

Actually, the includes file can be used to defined anything you want
Construct.py to know about. For example, you could define a function in that
file in which case that function is available to **call** in your
configuration file. Alternatively, you could even use:
```python
exec(open("some_file.py").read())
```
to import the contents of some Python file and evaluate it in the includes file.
By doing so, everything in `some_file.py` is available to Construct.py.

You can call any function defined in the includes file (see below) or use any
constant defined in the includes file in a configuration file.

Of course, sometimes we don't want this import file to be in the current
working directory. If you want to specify another directory to contain this
file, then you'll need to set the environment variable
`CONSTRUCT_PY_DIR` to the directory which contains the includes file. For
example, if `construct_py_includes.py` is located at
`~/some/other/directory/construct_py_includes.py`, then you'll need to set and
export `CONSTRUCT_PY_DIR=~/some/other/directory`. For example, you could
add the following to your `.zshrc`:
```zsh
export CONSTRUCT_PY_DIR=~/some/other/directory
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
`generic`    | Call any generic Python code such as `lambda x: x + 1`.
`side_effect`| Similar to `generic`, but replaces its node in the call tree with its child subtree. Used to apply function side-effects to a subtree.
`constant`   | Return a constant.
`arg_at`     | Indexes the arguments of the child tree
`kwarg_at`   | Indexes the keyword arguments of the child tree

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
function `f`, and so it would need to be defined in the includes file.

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
includes file. So, if you have the following module tree:
```
module X
	module Y
		function y
```
and you have the following in your includes file:
```python
import X
```
then to use `y` in a configuration file you need to specify it as `X.Y.y`. If
instead you import `Y` in your includes file, you can specify `y` as `Y.y`. If
you use `from X.Y import y` in your includes file, then you can specify `y` as
`y` in your configuration file. The general rule is that however you would
access the symbol `y` in your includes file, that's how `y` must be specified
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

A `constant` type takes one argument. If more than one argument is specified,
an error is raised.

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

A `generic` type takes one argument. If more than one argument is specified, an
error is raised.

### `side_effect` <a name="side_effect"></a>

With the `side_effect` type, we can call any arbitrary function with side effects. The
function will be run with the arguments and kwargs specified by the call tree
under the `side_effect` node. Once the `side_effect` has been completed, with its
side effects, the `side_effect` node will be replaced by its child subtree:


```
parent_tree --- side_effect node --- child_tree
```
will become:
```
parent_tree --- child_tree with side_effect applied
```

If the `side_effect` node is at the top of the CallTree, and it takes in a
single argument or kwarg, then the `side_effect` node is not replaced by its
child subtree, but is rather replaced by its single argument or kwarg.

The `side_effect` type is very similar to the `X` type, but doesn't construct
any object in the CallTree. Instead, it replaces itself with its child subtree.

The arguments to a `side_effect` type must start with the name of the function
to call (str). The arguments to the function to call must come after the name
of the function to call in the arguments for a `side_effect`. For example:

```toml
[0]
type = "side_effect"

[0.0]  # The name of the function to call
type = "constant"
args = ["function_to_call"]

[0.1]  # The first argument to the function to call
# ...

[0.2]  # The second argument to the function to call
# ...

[0.kwarg1]  # A kwarg to the function to call
# ...
```

### `arg_at/kwarg_at` <a name="arg_at/kwarg_at"></a>

The `arg_at` and `kwarg_at` types index the args/kwargs of their subtree. The
node containing an `arg_at`/`kwarg_at` is replaced by the indexed arg/kwarg.
This is most often useful in conjunction with they `side_effect` type. For
example, if a `side_effect` type is the root of the CallTree, then an
`arg_at`/`kwarg_at` can be used to extract a single value from the
`side_effect` and return that value as the value configured by the
configuration file.

The arguments to an `arg_at`/`kwarg_at` type are:
1. The index/keyword to access
2. The node to index the args/kwargs of

If more than 2 arguments are given, an error is raised.

## Calling Functions or Creating Objects Defined in the Code <a name="calling"></a>

One awesome feature is that if a function or object is defined in your Python
code, then that code can be called from the configuration file as long as that
code is available in your includes file!
Well, not exactly, but almost! Really, the configuration is deferred to
runtime, so when we create an object, we can just run some functions and put
the returned values in the call tree.

For example, if you have a function `f` defined in your
includes with a variable `x` defined in your includes file,
then you can call `f(x)` in your configuration file by using the `<-f(x)`
operator.

Two functions come bundled with Construct.py that can be called without
defining them in the includes file. These are `constant` and `generic` as
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

## __main__ <a name="__main__"></a>

There is an alternative way to run Construct.py. If you set the environment
variable `CONSTRUCT_PY_USE_MAIN` (to anything), then you can import anything from
the main module `__main__` when running Construct.py in addition to anything
defined in the includes file. Hence, if you import module `X` in your main
module, then there is no need to import `X` in the includes file. Construct.py
can automatically use it. There are two caveats:
1. You need to qualify any symbol `x` from the main module as `__main__.x` in
   your configuration files.
2. Although `CONSTRUCT_PY_USE_MAIN = true` makes Construct.py more powerful,
	you could very easily turn your program into a pretzel. Use caution!

## ToDo

- [ ] Docstrings
