# nary_rust

Typed, inert expression trees for Python, with the checking and node
construction written in Rust (PyO3).

- Every expression is an `Expr` and has a kind, `e.kind`. A kind is an object
  declared in Python with `kind(name)`: `NumberKind` and `BoolKind` here. A
  kind can also take other kinds as parameters,
  `TupleKind(NumberKind, BoolKind)`.
- A function declares the kinds it accepts and the kind it returns. The result
  is always of the declared kind; nothing is inferred from the arguments.
- A function can take any number of arguments of one kind (`rest=`).
- Expressions are inert: nothing is flattened, reordered or evaluated when an
  expression is built.

## Layout

| Path | What it is |
|---|---|
| `src/lib.rs` | The compiled module `nary._core`: `Expr`, `Kind`, `kind`, `KindFamily`, `kind_family`, `Function`, `function`, `set_operator`. It defines no particular kind and no particular function. |
| `python/nary/` | The package `nary`, the one to import. |
| `python/nary/__init__.py` | Re-exports the names of `nary._core` and everything listed in the `__all__` of the modules below, so a name added to one of those lists is `nary.<name>` with no change here. |
| `python/nary/kinds.py` | Declares the kinds `NumberKind` and `BoolKind` with `kind(...)`. |
| `python/nary/arithmetic.py` | Declares `Add`, `Mul` and `Pow` with `function(...)`, and sets what `+` and `*` build for a `NumberKind`. |
| `python/nary/elementary.py` | Declares `sin`. |
| `python/nary/relational.py` | Declares `Lt` and `Eq`, and sets what `<` builds for a `NumberKind`. |
| `tests/` | The tests. |
| `bench/` | `bench_construct.py` times building, comparing and hashing expressions. `compare.py` runs it on several versions and prints their ratios. |

## Build

Needs a Rust toolchain and [uv](https://docs.astral.sh/uv/).

    uv venv
    uvx maturin develop -r

This builds the compiled module as `python/nary/_core` and installs the
package `nary` into `.venv`, linked to `python/`, so an edit to a Python file
needs no rebuild. To run the tests:

    uv pip install pytest
    .venv/bin/python -m pytest

To build a wheel instead, for the Python in `.venv`:

    uvx maturin build -r -i .venv/bin/python

The wheel is written to `target/wheels/`. It contains the package `nary`,
with the compiled module in it.

## Use

```python
>>> import nary as nr
>>> x, y, z = (nr.NumberKind(n) for n in "xyz")

>>> nr.Add(x, y, z)                  # any number of arguments
Add(x, y, z)
>>> x + y + z                        # operators build two-argument nodes
Add(Add(x, y), z)
>>> nr.sin(x) * y < z                # a comparison is a BoolKind
Lt(Mul(sin(x), y), z)
>>> (x + y).kind, (x < y).kind
(NumberKind, BoolKind)

>>> eq = nr.Eq(x + y, z)             # named arguments
>>> eq.lhs, eq.rhs
(Add(x, y), z)

>>> nr.sin(x < y)
Traceback (most recent call last):
    ...
TypeError: sin expects NumberKind, got BoolKind: Lt(x, y)
>>> nr.Pow(x, y, z)
Traceback (most recent call last):
    ...
TypeError: Pow takes 2 arguments, got 3

```

Declaring a function:

```python
>>> from nary import BoolKind, NumberKind, function

>>> cos = function("cos", NumberKind, returns=NumberKind)
>>> Max = function("Max", rest=NumberKind, returns=NumberKind)
>>> Le = function("Le", NumberKind, NumberKind, returns=BoolKind, names=("lhs", "rhs"))

>>> Le.name, Le.params, Le.rest, Le.returns, Le.names     # what was declared
('Le', (NumberKind, NumberKind), None, BoolKind, ('lhs', 'rhs'))
>>> Max.params, Max.rest, Max.names
((), NumberKind, ())

```

## Kinds

A kind is declared in Python, and adding one needs no change in Rust:

```python
>>> from nary import kind, set_operator

>>> SetKind = kind("SetKind")
>>> Union = function("Union", rest=SetKind, returns=SetKind)
>>> Contains = function("Contains", NumberKind, SetKind, returns=BoolKind)
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
>>> SetKind("Union", S, T)                   # only a function builds a node
Traceback (most recent call last):
    ...
TypeError: SetKind takes 1 argument, the name of a leaf, got 3; a node is built by calling a function

```

- Calling a kind takes one argument, the name, and makes a leaf, whose
  `args` is `()`. Any further argument is a `TypeError`. A node with
  arguments is built only by calling a declared function (directly or
  through an operator), so every argument of every node is an `Expr` that
  passed that function's kind check.
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
  not support it: `p + q` on two `BoolKind`s is a `TypeError`.

## Parametrised kinds

A kind family is declared with `kind_family(name)`, and calling it with kinds
as parameters gives a kind. Such a kind is like any other: it can be used in
a signature, it has its own operators, and calling it makes a leaf.

```python
>>> from nary import kind_family

>>> TupleKind = kind_family("TupleKind")              # one or more parameters
>>> MatrixKind = kind_family("MatrixKind", params=1)  # exactly one parameter

>>> Pair = TupleKind(NumberKind, BoolKind)
>>> Pair
TupleKind(NumberKind, BoolKind)
>>> Pair is TupleKind(NumberKind, BoolKind)           # the same kind every time
True
>>> Pair.family, Pair.params
(<kind family TupleKind>, (NumberKind, BoolKind))
>>> TupleKind(MatrixKind(NumberKind), Pair)           # parameters can be parametrised
TupleKind(MatrixKind(NumberKind), TupleKind(NumberKind, BoolKind))

>>> Piece = function("Piece", NumberKind, BoolKind, returns=Pair)
>>> Piece(x, x < y).kind is Pair
True

>>> Matrix = MatrixKind(NumberKind)
>>> MatMul = function("MatMul", rest=Matrix, returns=Matrix)
>>> Trace = function("Trace", Matrix, returns=NumberKind)
>>> set_operator(Matrix, "*", MatMul)
>>> A, B = Matrix("A"), Matrix("B")
>>> Trace(A * B)
Trace(MatMul(A, B))
>>> Trace(MatrixKind(BoolKind)("P"))
Traceback (most recent call last):
    ...
TypeError: Trace expects MatrixKind(NumberKind), got MatrixKind(BoolKind): P
>>> MatrixKind(NumberKind, BoolKind)
Traceback (most recent call last):
    ...
TypeError: MatrixKind takes 1 parameter, got 2

```

- A family returns the same kind object whenever it is given the same
  parameters in the same order, so kinds are still compared by identity. A
  family looks its kinds up in a table, guarded by a lock, only when it is
  called. Nodes of a parametrised kind are built, compared and hashed exactly
  as nodes of any other kind.
- A kind made by a family lasts for the life of the process, as any kind
  does, and so does its family. Each different list of parameters makes one
  more kind, so instantiate families when a module is imported, not with
  parameters that keep changing.
- `kind.family` and `kind.params` are `None` and `()` for a kind declared
  with `kind(name)`. A family has `name`, and `params`, the number of
  parameters it takes or `None`.
- Every `kind_family(...)` call makes a new family, even with a name already
  used, and its kinds are different from those of any other family.

## Limitations

- The three operators (`+`, `*`, `<`) are fixed in Rust. `set_operator` can be
  called once for each kind and operator.
- A kind is only a name and its operators. It cannot have methods or
  attributes of its own, and there are no kinds of kinds.
- The parameters of a kind family can only be kinds. A matrix shape or any
  other value cannot be a parameter.
- Nothing builds values of a family's kinds automatically. A Python tuple is
  not turned into an expression where a `TupleKind(...)` is expected; values
  are built by declared functions, such as `Piece` above.
- There are no generic functions and no kind variables: a function is
  declared for particular kinds, and one function cannot accept every
  `MatrixKind(...)`. Working out a result kind from the arguments would be
  inference, which this package does not do.
- The package declares no families and no functions on them.
- `==` compares structure and returns a Python `bool`; it does not build an
  `Eq`. `x + y + z` is not equal to `Add(x, y, z)`.
- Equal expressions are not shared, so equality walks both trees.
- A leaf can be given any name, including the name of a function, so
  `NumberKind("Add")` is equal to `Add()`, the call of `Add` with no
  arguments: a leaf and a node with no arguments are not told apart.
