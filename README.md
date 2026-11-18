# nary_rust

Typed, inert expression trees for Python, with the checking and node
construction written in Rust (PyO3).

- Every expression is an `Expr` and has a kind, `e.kind`. A kind is an object
  declared in Python with `kind(name)`: `NumberKind` and `BoolKind` here. A
  kind can also take other kinds as parameters,
  `TupleKind(NumberKind, BoolKind)`.
- Every expression is one of four forms: a symbol (`NumberKind("x")`), a
  declared function (`sin`), an application of a head expression to
  arguments (`sin(x)`), or a lambda (`Lambda(x, sin(x))`).
- A function is an expression whose kind is a function kind,
  `FunctionKind(inputs, output)`. Calling it checks the kinds of the
  arguments and builds an application of the output kind; nothing is
  inferred from the arguments.
- A function can take any number of arguments of one kind (`rest=`).
- Expressions are inert: nothing is flattened, reordered or evaluated when an
  expression is built.

## Layout

| Path | What it is |
|---|---|
| `src/lib.rs` | The compiled module `nary._core`: `Expr`, `Kind`, `kind`, `KindFamily`, `kind_family`, `FunctionKind`, `function`, `Lambda`, `set_operator`. It defines no kind other than the function kinds, and no particular function. |
| `python/nary/` | The package `nary`, the one to import. |
| `python/nary/__init__.py` | Re-exports the names of `nary._core` and everything listed in the `__all__` of the modules below, so a name added to one of those lists is `nary.<name>` with no change here. |
| `python/nary/kinds.py` | Declares the kinds `NumberKind` and `BoolKind` with `kind(...)`. |
| `python/nary/arithmetic.py` | Declares `Add`, `Mul` and `Pow` with `function(...)`, and sets what `+`, `*` and `**` build for a `NumberKind`. |
| `python/nary/elementary.py` | Declares `sin`. |
| `python/nary/relational.py` | Declares `Lt`, `Gt`, `Le`, `Ge` and `Eq`, and sets what `<`, `>`, `<=` and `>=` build for a `NumberKind`. |
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
>>> x ** y >= z                      # also >, <=
Ge(Pow(x, y), z)

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

## Functions

A declared function is an expression: a named constant whose kind is a
function kind. `function(name, *inputs, rest=None, returns, names=None)`
declares one.

```python
>>> from nary import BoolKind, FunctionKind, NumberKind, function

>>> cos = function("cos", NumberKind, returns=NumberKind)
>>> Max = function("Max", rest=NumberKind, returns=NumberKind)
>>> Le = function("Le", NumberKind, NumberKind, returns=BoolKind, names=("lhs", "rhs"))

>>> Le, Le.kind
(Le, FunctionKind((NumberKind, NumberKind), BoolKind))
>>> Le.kind.inputs, Le.kind.rest, Le.kind.output, Le.names
((NumberKind, NumberKind), None, BoolKind, ('lhs', 'rhs'))
>>> Max.kind
FunctionKind((), NumberKind, rest=NumberKind)
>>> cos.kind is FunctionKind((NumberKind,), NumberKind)   # the same kind every time
True

```

Calling any expression of a function kind builds an application, whose
`head` is the expression called. Calling a function kind with a name makes
a symbol of that kind, an unknown function, and a function can be passed
where its kind is expected:

```python
>>> f = FunctionKind((NumberKind,), NumberKind)("f")
>>> f(x) + cos(x)
Add(f(x), cos(x))
>>> f(x).head is f, f(x).args, cos(x).head is cos
(True, (x,), True)

>>> At = function("At", f.kind, NumberKind, returns=NumberKind)
>>> At(cos, x), At(f, y)
(At(cos, x), At(f, y))
>>> At(nr.Lt, x)
Traceback (most recent call last):
    ...
TypeError: At expects FunctionKind((NumberKind,), NumberKind), got FunctionKind((NumberKind, NumberKind), BoolKind): Lt
>>> x(y)
Traceback (most recent call last):
    ...
TypeError: x is of kind NumberKind, which is not a function kind, so it cannot be called

```

`Lambda(variables, body)` is the one binder. `variables` is a symbol or a
tuple of different symbols, and the kind of the lambda is the function kind
from their kinds to the kind of the body. Applying a lambda builds an
application like any other; nothing is substituted.

```python
>>> from nary import Lambda

>>> square = Lambda(x, x * x)
>>> square, square.kind
(Lambda(x, Mul(x, x)), FunctionKind((NumberKind,), NumberKind))
>>> Lambda((x, y), x < y).kind
FunctionKind((NumberKind, NumberKind), BoolKind)
>>> square(z), At(square, z)
(Lambda(x, Mul(x, x))(z), At(Lambda(x, Mul(x, x)), z))
>>> square.variables, square.body
((x,), Mul(x, x))
>>> Lambda(cos, x)
Traceback (most recent call last):
    ...
TypeError: Lambda variables must be symbols, got declared function cos

```

- `e.head` is the head expression of an application and `None` otherwise;
  `e.args` is the arguments of an application and `()` otherwise; `e.name`
  is the name of a symbol or declared function and `None` otherwise.
  `e.is_symbol` and `e.is_lambda` tell those forms apart, and a lambda has
  `variables` (always a tuple) and `body`.
- Named arguments such as `eq.lhs` are looked up through the `names` of
  the head of an application.
- `FunctionKind(inputs, output, rest=None)` takes a tuple of kinds, possibly
  empty, and one kind. The same arguments give the same kind, so function
  kinds are compared by identity like any other. They can nest, and can be
  parameters of kind families. For any other kind, `inputs`, `rest` and
  `output` are `None`.
- Every `function(...)` call makes a new function, even with a name and
  kind already used, and a declared function is equal only to itself.
- Symbols are equal when they have the same kind and name, applications when
  their heads and arguments are equal, and lambdas when their variables and
  bodies are equal. Expressions of different forms are never equal.

## Kinds

A kind is declared in Python, and adding one needs no change in Rust:

```python
>>> from nary import kind, set_operator

>>> SetKind = kind("SetKind")
>>> Union = function("Union", rest=SetKind, returns=SetKind)
>>> Contains = function("Contains", NumberKind, SetKind, returns=BoolKind)
>>> set_operator(SetKind, "+", Union)        # what + builds for two sets

>>> S, T = SetKind("S"), SetKind("T")        # calling a kind makes a symbol
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

- Calling a kind takes one argument, the name, and makes a symbol, whose
  `args` is `()`. Any further argument is a `TypeError`. A node with
  arguments is built only by calling an expression of a function kind
  (directly or through an operator), so every argument of every node is an
  `Expr` that passed the kind check of its head.
- There is one class of expression, `Expr`, whatever the kind. Test the kind
  with `e.kind is NumberKind`. A kind is not a class, so
  `isinstance(e, NumberKind)` is an error, and `Expr` cannot be subclassed.
- A kind lasts for the life of the process, and an expression refers to it
  without reference counting. Building an expression costs the same whatever
  the kind and however many kinds there are.
- Every `kind(...)` call makes a new kind, even with a name already used.
  Declare each kind once, when a module is imported.
- `set_operator(kind, symbol, function)` says what an operator builds when its
  left operand is of that kind. The function is any expression of a
  function kind. A kind with no function for an operator does
  not support it: `p + q` on two `BoolKind`s is a `TypeError`.

## Parametrised kinds

A kind family is declared with `kind_family(name)`, and calling it with kinds
as parameters gives a kind. Such a kind is like any other: it can be used in
a signature, it has its own operators, and calling it makes a symbol.

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
  with `kind(name)` and for a function kind. A family has `name`, and
  `params`, the number of parameters it takes or `None`.
- Every `kind_family(...)` call makes a new family, even with a name already
  used, and its kinds are different from those of any other family.

## Limitations

- The seven operators (`+`, `*`, `**`, `<`, `>`, `<=`, `>=`) are fixed in
  Rust. There are no reflected operators (`1 + x`), and no `-` or `/`.
  `set_operator` can be called once for each kind and operator.
- A kind is only a name and its operators (and, for a function kind, its
  inputs and output). It cannot have methods or attributes of its own, and
  there are no kinds of kinds.
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
- Lambdas are equal only with the same variable names: `Lambda(x, x)` is
  not equal to `Lambda(y, y)`. There is no equality up to renaming.
- There is no substitution, no beta reduction and no free-variable or
  renaming operation. Applying a lambda is inert.
- A symbol, a declared function and an application of a named head to no
  arguments can all print the same: `NumberKind("Add")`, `Add` and `Add()`
  all print as `Add`, though none is equal to another.
