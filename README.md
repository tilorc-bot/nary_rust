# nary_rust

Typed, inert expression trees for Python, with the checking and node
construction written in Rust (PyO3).

- Every expression is an `Expr` and has a kind, `e.kind`. A kind is an object
  declared in Python with `kind(name)`: `NumberKind` and `BoolKind` here. A
  kind family, declared with `kind_family(name)`, gives a kind for each list
  of kinds it is given as parameters: `SetKind(NumberKind)`,
  `MatrixKind(NumberKind)`.
- A function declares the kinds it accepts and the kind it returns. The result
  is always of the declared kind; nothing is inferred from the arguments.
- A function can take any number of arguments of one kind, or any number of
  repeats of a group of kinds (`rest=`).
- A position can require a symbol, and a function can record which of its
  arguments is a bound variable.
- Expressions are inert: nothing is flattened, reordered or evaluated when an
  expression is built.

## Layout

| Path | What it is |
|---|---|
| `src/lib.rs` | The compiled module `nary._core`: `Expr`, `Kind`, `kind`, `KindFamily`, `kind_family`, `Integer`, `Symbol`, `Function`, `function`, `set_operator`, `set_integer_kind`. It defines no particular kind, family or function. |
| `python/nary/` | The package to import. `kinds` declares the kinds with `kind(...)` and the families with `kind_family(...)`. The other modules declare functions with `function(...)`: `arithmetic`, `elementary`, `relational`, `logic`, `piecewise`, `calculus`, `sets`, `matrices`. `arithmetic`, `relational` and `matrices` also set which function each operator builds for a kind. |
| `tests/` | The tests. `tests/test_readme.py` runs the examples below. |
| `bench/` | `bench_construct.py` times building, comparing and hashing expressions. `compare.py` runs it on several versions and prints their ratios. |

## Build

Needs a Rust toolchain and [uv](https://docs.astral.sh/uv/).

    uv venv
    uvx maturin develop -r

This builds the package and installs it into `.venv`. To run the tests:

    uv pip install pytest
    .venv/bin/python -m pytest

To build a wheel instead, for the Python in `.venv`:

    uvx maturin build -r -i .venv/bin/python

The wheel is written to `target/wheels/`. It is named `nary_rust` and installs
the package `nary`.

## Use

```python
>>> import nary as nr
>>> x, y, z = (nr.NumberKind(n) for n in "xyz")   # symbols

>>> nr.Add(x, y, z)                  # any number of arguments
Add(x, y, z)
>>> x + y + z                        # operators build two-argument nodes
Add(Add(x, y), z)
>>> 2 * x**2 + 1                     # a Python int becomes an Integer
Add(Mul(2, Pow(x, 2)), 1)
>>> nr.sin(x) * y <= z               # a comparison is a BoolKind
Le(Mul(sin(x), y), z)
>>> (x + y).kind, (x <= y).kind
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

Calling a kind makes a symbol of that kind. A set of numbers is of the kind
`SetKind(NumberKind)` and a matrix of numbers of the kind
`MatrixKind(NumberKind)`, and each has its own functions. For a matrix, `+`
and `*` build the matrix functions:

```python
>>> Set, Matrix = nr.SetKind(nr.NumberKind), nr.MatrixKind(nr.NumberKind)
>>> Set, Matrix
(SetKind(NumberKind), MatrixKind(NumberKind))
>>> S, A, B = Set("S"), Matrix("A"), Matrix("B")
>>> nr.Contains(x, nr.Union(nr.Interval(0, 1), S))
Contains(x, Union(Interval(0, 1), S))
>>> nr.Determinant(nr.MatMul(A, nr.Transpose(B)))
Determinant(MatMul(A, Transpose(B)))
>>> A * B + A, x * y + x
(MatAdd(MatMul(A, B), A), Add(Mul(x, y), x))
>>> (A * B).kind is Matrix
True
>>> A * x
Traceback (most recent call last):
    ...
TypeError: MatMul expects MatrixKind(NumberKind), got NumberKind: x

```

`Piecewise` takes its values and conditions alternately:

```python
>>> nr.Piecewise(x, x > 0, nr.Mul(-1, x), nr.true)
Piecewise(x, Gt(x, 0), Mul(-1, x), true)
>>> nr.Piecewise(x, x > 0, y)
Traceback (most recent call last):
    ...
TypeError: Piecewise takes arguments in groups of 2, got 3

```

Integrals, sums and the like take a variable, which must be a symbol. Their
arguments are written flat, and several variables are written by nesting:

```python
>>> nr.Integral(nr.sin(x), x, 0, nr.pi)
Integral(sin(x), x, 0, pi)
>>> nr.Integral(nr.Integral(x * y, x, 0, 1), y, 0, 2)
Integral(Integral(Mul(x, y), x, 0, 1), y, 0, 2)
>>> nr.Derivative(nr.sin(x), x)
Derivative(sin(x), x)
>>> nr.Integral(x, x + y, 0, 1)
Traceback (most recent call last):
    ...
TypeError: Integral expects a NumberKind symbol, got NumberKind: Add(x, y)
>>> nr.Integral(x, nr.pi, 0, 1)      # a constant is not a symbol
Traceback (most recent call last):
    ...
TypeError: Integral expects a NumberKind symbol, got NumberKind: pi

```

## Declaring a function

```python
>>> from nary import BoolKind, NumberKind, SetKind, Symbol, function

>>> sinh = function("sinh", NumberKind, returns=NumberKind)
>>> Max = function("Max", rest=NumberKind, returns=NumberKind)
>>> Ne = function("Ne", NumberKind, NumberKind, returns=BoolKind, names=("lhs", "rhs"))
>>> ImageSet = function(
...     "ImageSet", NumberKind, Symbol(NumberKind), SetKind(NumberKind),
...     returns=SetKind(NumberKind), names=("expr", "var", "base"), binds={1: (0,)},
... )
>>> ImageSet(x**2, x, nr.Interval(0, 1))
ImageSet(Pow(x, 2), x, Interval(0, 1))

```

- The positional arguments after the name are the kinds of the leading
  arguments. `Symbol(kind)` is a position that accepts only a symbol of that
  kind. Any kind will do, including one made by a family:
  `Symbol(MatrixKind(NumberKind))`.
- `returns=` is the kind of the result.
- `rest=` is a kind, or a tuple of kinds that repeats as a group:
  `rest=(NumberKind, BoolKind)` accepts any number of (number, condition)
  pairs.
- `names=` gives attribute names to the leading arguments. A name that every
  expression already has, such as `kind` or `value`, is refused.
- `binds={1: (0,)}` records that argument 1 is a variable bound in argument 0.
  It is kept on the function and nothing reads it yet:

```python
>>> nr.Integral.binds                # x is bound in the body, not the limits
{1: (0,)}
>>> nr.Derivative.binds              # the variable of a derivative stays free
{}

```

An expression has `kind`, `head`, `args`, `is_symbol`, `is_integer` and
`value`. A symbol, an integer and a function applied to arguments are told
apart, even when the head and the arguments are the same:

```python
>>> e = x + 1
>>> e.kind, e.head, e.args
(NumberKind, 'Add', (x, 1))
>>> e.args[0].is_symbol, e.args[1].is_integer, e.args[1].value
(True, True, 1)
>>> nr.pi.is_symbol
False
>>> NumberKind("Add") == nr.Add()    # a symbol named Add, and Add of nothing
False

```

## Declaring a kind

A kind is declared in Python, and adding one needs no change in Rust. The
kinds of the package are declared this way in `python/nary/kinds.py`.

```python
>>> from nary import kind, set_operator

>>> VectorKind = kind("VectorKind")
>>> VecAdd = function("VecAdd", rest=VectorKind, returns=VectorKind)
>>> Dot = function("Dot", VectorKind, VectorKind, returns=NumberKind)
>>> set_operator(VectorKind, "+", VecAdd)    # what + builds for two vectors

>>> u, v = VectorKind("u"), VectorKind("v")  # calling a kind makes a symbol
>>> Dot(u + v, u) + 1
Add(Dot(VecAdd(u, v), u), 1)
>>> (u + v).kind is VectorKind
True
>>> Dot(u, x)
Traceback (most recent call last):
    ...
TypeError: Dot expects VectorKind, got NumberKind: x
>>> VectorKind("VecAdd", u, v)               # only a function builds a node
Traceback (most recent call last):
    ...
TypeError: VectorKind takes 1 argument, the name of a leaf, got 3; a node is built by calling a function

```

- Calling a kind takes one argument, the name, and makes a symbol, whose
  `args` is `()`. Any further argument is a `TypeError`. A node with
  arguments is built only by calling a declared function (directly or
  through an operator), so every argument of every node is an `Expr` that
  passed that function's kind check, or a Python int that was converted
  where an integer was expected.
- There is one class of expression, `Expr`, whatever the kind. Test the kind
  with `e.kind is NumberKind`. A kind is not a class, so
  `isinstance(e, NumberKind)` is an error, and `Expr` cannot be subclassed.
- A kind lasts for the life of the process, and an expression refers to it
  without reference counting. Building an expression costs the same whatever
  the kind and however many kinds there are.
- Every `kind(...)` call makes a new kind, even with a name already used.
  Declare each kind once, when a module is imported.
- `set_operator(kind, symbol, function)` says what an operator builds when its
  operand is of that kind: the left operand, or the right one when the left
  is not an expression, as in `2 * x`. A kind with no function for an operator
  does not support it: `p + q` on two `BoolKind`s is a `TypeError`.
- `set_integer_kind(NumberKind)` says which kind an integer is. It is said
  once, in `python/nary/kinds.py`. A Python int is converted only where that
  kind is expected.

## Kind families

A kind family is declared with `kind_family(name)`, and calling it with kinds
as parameters gives a kind. Such a kind is like any other: it can be used in
a signature, it has its own operators, and calling it makes a symbol. The
package declares two families with one parameter each, `SetKind` and
`MatrixKind`, and has functions only for `SetKind(NumberKind)` and
`MatrixKind(NumberKind)`.

```python
>>> from nary import MatrixKind, kind_family

>>> MatrixKind
<kind family MatrixKind>
>>> MatrixKind(NumberKind) is Matrix                 # the same kind every time
True
>>> Matrix.family, Matrix.params
(<kind family MatrixKind>, (NumberKind,))
>>> Trace = function("Trace", Matrix, returns=NumberKind)
>>> Trace(A * B)
Trace(MatMul(A, B))
>>> Trace(MatrixKind(BoolKind)("P"))                  # another kind of the family
Traceback (most recent call last):
    ...
TypeError: Trace expects MatrixKind(NumberKind), got MatrixKind(BoolKind): P
>>> MatrixKind(NumberKind, BoolKind)
Traceback (most recent call last):
    ...
TypeError: MatrixKind takes 1 parameter, got 2

>>> TupleKind = kind_family("TupleKind")              # one or more parameters
>>> Pair = TupleKind(NumberKind, BoolKind)
>>> Pair
TupleKind(NumberKind, BoolKind)
>>> TupleKind(Matrix, Pair)                           # parameters can be parametrised
TupleKind(MatrixKind(NumberKind), TupleKind(NumberKind, BoolKind))
>>> Piece = function("Piece", NumberKind, BoolKind, returns=Pair)
>>> Piece(x, x < y).kind is Pair
True

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

- The seven operators (`+`, `*`, `**`, `<`, `>`, `<=`, `>=`) are fixed in
  Rust. `set_operator` can be called once for each kind and operator.
- There is no `-` or `/`. Write `Add(x, Mul(-1, y))` and `Mul(x, Pow(y, -1))`.
- A kind is only a name and its operators. It cannot have methods or
  attributes of its own, and there are no kinds of kinds.
- The parameters of a kind family can only be kinds. A matrix shape or any
  other value cannot be a parameter, so a matrix kind does not record its
  shape.
- There are no generic functions and no kind variables: a function is
  declared for particular kinds, and one function cannot accept every
  `MatrixKind(...)`. Working out a result kind from the arguments would be
  inference, which this package does not do. `SetKind(BoolKind)` or
  `MatrixKind(BoolKind)` can be made, but no function of the package accepts
  them, and they have no operators.
- Nothing builds values of a family's kinds automatically. A Python tuple is
  not turned into an expression where a `TupleKind(...)` is expected; values
  are built by declared functions, such as `Piece` above.
- A number times a matrix has no function: `2 * A` and `x * A` are errors.
- With an int on the left, a comparison is built the other way round: `1 < x`
  is `Gt(x, 1)`.
- The only numbers are integers. A Python `float` or `bool` is not converted.
- The package declares no tuple kind and no function kind. `Lambda`, passing
  a function itself as an argument, and derivatives of order n or in several
  variables at once are left out.
- `==` compares structure and returns a Python `bool`; it does not build an
  `Eq`. `x + y + z` is not equal to `Add(x, y, z)`.
- Bound variables are recorded but not used: `Integral(x, x, 0, 1)` is not
  equal to `Integral(y, y, 0, 1)`.
- Equal expressions are not shared, so equality walks both trees.
- A head is a string. Two functions declared with the same name and the same
  returned kind build equal nodes.
