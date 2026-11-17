# nary_rust

Typed, inert expression trees for Python, with the checking and node
construction written in Rust (PyO3).

- Every expression is an `Expr` and has a kind, `e.kind`. A kind is an object
  declared in Python with `kind(name)`: `NumberKind` and `Bool` here.
- A function declares the kinds it accepts and the kind it returns. The result
  is always of the declared kind; nothing is inferred from the arguments.
- A function can take any number of arguments of one kind (`rest=`).
- Expressions are inert: nothing is flattened, reordered or evaluated when an
  expression is built.

## Layout

| Path | What it is |
|---|---|
| `src/lib.rs` | The compiled module `nary_rust`: `Expr`, `Kind`, `kind`, `Function`, `function`, `set_operator`. It defines no particular kind and no particular function. |
| `nary_rs.py` | Declares the kinds `NumberKind` and `Bool` with `kind(...)` and the functions `Add`, `Mul`, `Pow`, `sin`, `Lt` and `Eq` with `function(...)`, and sets which function each operator builds for each kind. This is the module to import. |
| `tests/` | The tests. |
| `bench/` | `bench_construct.py` times building, comparing and hashing expressions. `compare.py` runs it on several versions and prints their ratios. |

## Build

Needs a Rust toolchain and [uv](https://docs.astral.sh/uv/).

    uv venv
    uvx maturin develop -r

This builds the compiled module and installs it into `.venv`. `nary_rs.py` is
not installed; it is used from this directory. To run the tests:

    uv pip install pytest
    .venv/bin/python -m pytest

To build a wheel instead, for the Python in `.venv`:

    uvx maturin build -r -i .venv/bin/python

The wheel is written to `target/wheels/`. It contains only the compiled
module.

## Use

```python
>>> import nary_rs as nr
>>> x, y, z = (nr.NumberKind(n) for n in "xyz")

>>> nr.Add(x, y, z)                  # any number of arguments
Add(x, y, z)
>>> x + y + z                        # operators build two-argument nodes
Add(Add(x, y), z)
>>> nr.sin(x) * y < z                # a comparison is a Bool
Lt(Mul(sin(x), y), z)
>>> (x + y).kind, (x < y).kind
(NumberKind, Bool)

>>> eq = nr.Eq(x + y, z)             # named arguments
>>> eq.lhs, eq.rhs
(Add(x, y), z)

>>> nr.sin(x < y)
Traceback (most recent call last):
    ...
TypeError: sin expects NumberKind, got Bool: Lt(x, y)
>>> nr.Pow(x, y, z)
Traceback (most recent call last):
    ...
TypeError: Pow takes 2 arguments, got 3

```

Declaring a function:

```python
>>> from nary_rs import Bool, NumberKind, function

>>> cos = function("cos", NumberKind, returns=NumberKind)
>>> Max = function("Max", rest=NumberKind, returns=NumberKind)
>>> Le = function("Le", NumberKind, NumberKind, returns=Bool, names=("lhs", "rhs"))

```

## Kinds

A kind is declared in Python, and adding one needs no change in Rust:

```python
>>> from nary_rs import kind, set_operator

>>> SetKind = kind("SetKind")
>>> Union = function("Union", rest=SetKind, returns=SetKind)
>>> Contains = function("Contains", NumberKind, SetKind, returns=Bool)
>>> set_operator(SetKind, "+", Union)        # what + builds for two sets

>>> S, T = SetKind("S"), SetKind("T")        # calling a kind makes a leaf
>>> Contains(x, S + T)
Contains(x, Union(S, T))
>>> (S + T).kind is SetKind
True
>>> Union(S, x)
Traceback (most recent call last):
    ...
TypeError: Union expects SetKind, got NumberKind: x

```

- There is one class of expression, `Expr`, whatever the kind. Test the kind
  with `e.kind is NumberKind`. A kind is not a class, so
  `isinstance(e, NumberKind)` is an error, and `Expr` cannot be subclassed.
- A kind lasts for the life of the process, and an expression refers to it
  without reference counting. Building an expression costs the same whatever
  the kind and however many kinds there are.
- Every `kind(...)` call makes a new kind, even with a name already used.
  Declare each kind once, when a module is imported.
- `set_operator(kind, symbol, function)` says what an operator builds when its
  left operand is of that kind. A kind with no function for an operator does
  not support it: `p + q` on two `Bool`s is a `TypeError`.

## Limitations

- The three operators (`+`, `*`, `<`) are fixed in Rust. `set_operator` can be
  called once for each kind and operator.
- A kind is only a name and its operators. It cannot have methods or
  attributes of its own, and there are no kinds of kinds.
- `==` compares structure and returns a Python `bool`; it does not build an
  `Eq`. `x + y + z` is not equal to `Add(x, y, z)`.
- Equal expressions are not shared, so equality walks both trees.
