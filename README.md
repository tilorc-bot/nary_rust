# nary_rust

Typed, inert expression trees for Python, with the checking and node
construction written in Rust (PyO3).

- Every expression is an `Expr` and has a kind, `e.kind`. A kind is an object
  declared in Python with `declare_kind(name)`: `NumberKind` and `BoolKind`
  here. A kind can also take other kinds as parameters,
  `TupleKind(NumberKind, BoolKind)`.
- Every expression is one of four forms: a symbol (`NumberKind("x")`), a
  literal holding a Python value (`NumberKind(3)`), a declared constant
  (`pi`), or an application of a head expression to arguments (`sin(x)`). A
  declared function (`sin`) is a declared constant whose kind is a function
  kind.
- A kind declares which Python values are its literals,
  `declare_kind("NumberKind", literals=int)`, and such a value passed where
  that kind is expected becomes a literal of it: `sin(1)`, `x + 1`.
- A function is an expression whose kind is a function kind,
  `FunctionKind(inputs, output)`. Calling it checks the kinds of the
  arguments and builds an application of the output kind; nothing is
  inferred from the arguments.
- A function can take any number of arguments of one kind (`rest=`), and a
  leading position can accept only a symbol (`Symbol(kind)`).
- `Lambda` is defined in Python, in `nary/functions.py`, as an ordinary
  application built with those mechanisms.
- Expressions are inert: nothing is flattened, reordered or evaluated when an
  expression is built.

## Layout

| Path | What it is |
|---|---|
| `src/lib.rs` | The compiled module `nary._core`: `Expr`, `Kind`, `declare_kind`, `KindFamily`, `declare_kind_family`, `FunctionKind`, `declare_function`, `declare_constant`, `Symbol`, `set_operator`. It defines no kind other than the function kinds, and no particular function or constant. |
| `python/nary/` | The package `nary`, the one to import. |
| `python/nary/__init__.py` | Re-exports the names of `nary._core` and everything listed in the `__all__` of the modules below, so a name added to one of those lists is `nary.<name>` with no change here. |
| `python/nary/kinds.py` | Declares the kinds `NumberKind` (whose literals are `int`s) and `BoolKind` with `declare_kind(...)`. |
| `python/nary/arithmetic.py` | Declares `Add`, `Mul`, `Pow` and the literal `NegativeOne` (`-1`), sets what `+`, `-`, `*`, `/`, `**` and unary minus build for a `NumberKind`, and records the domain of `Pow`. |
| `python/nary/elementary.py` | Declares `sin`, `cos`, `tan`, `exp`, `log` and `re`, and records the domains of `log` and `tan`. |
| `python/nary/constants.py` | Declares the constants `pi`, `E` and `I`. |
| `python/nary/functions.py` | Defines `Lambda` and `is_lambda`, with `declare_function(...)` and `Symbol(kind)`. |
| `python/nary/domains.py` | `set_domain(...)` and `domain(...)`: records the domain of a partial function, the condition under which it has a value. Not re-exported; import it as `nary.domains`. |
| `python/nary/relational.py` | Declares `Lt`, `Gt`, `Le`, `Ge`, `Eq` and `Ne`, and sets what `<`, `>`, `<=` and `>=` build for a `NumberKind`. |
| `python/nary/sets.py` | Declares the kind family `SetKind`, the kind `NumberSet = SetKind(NumberKind)`, the constants `Reals` and `Integers`, and `Contains`, `FiniteSet`, `Union` and `Intersection`, so that "x is real" is `Contains(x, Reals)`. Not re-exported; import it as `nary.sets`. |
| `python/nary/lean.py` | `to_lean(...)` and `to_lean_example(...)`: write an expression as the Lean term built from the definitions in `lean/`. `to_lean_rule(...)` and `to_lean_facts(...)`: write a rule, or the facts about a function, as a Lean statement. Not re-exported; import it as `nary.lean`. See `lean/README.md`. |
| `lean/` | A separate Lean 4 project (with Mathlib) that defines what the functions declared in `python/nary/` mean, where each has a value, and proves the rules and facts of `python/nary/arithmetic_rules.py`, whose statements are generated from Python by `lean/generate_rules.py`. See `lean/README.md`. |
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

CI (`.github/workflows/ci.yml`) runs these tests, `lake build` in `lean/`
and `lean/check_printer.py` on every pull request and push to `main`.

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

## Subtraction, division and negation

There are no `Sub`, `Div` or `Neg` functions. As in SymPy, `-`, `/` and
unary minus are built from `Add`, `Mul`, `Pow` and the literal `-1`, by
Python functions in `nary/arithmetic.py` given to `set_operator`. Unary
minus is spelled `"neg"`.

```python
NegativeOne = NumberKind(-1)

def _subtract(a, b):   # a - b
    return Add(a, Mul(NegativeOne, b))

def _divide(a, b):     # a / b
    return Mul(a, Pow(b, NegativeOne))

def _negate(a):        # -a
    return Mul(NegativeOne, a)

set_operator(NumberKind, "-", _subtract)
set_operator(NumberKind, "/", _divide)
set_operator(NumberKind, "neg", _negate)
```

```python
>>> x - y, x / y, -x
(Add(x, Mul(-1, y)), Mul(x, Pow(y, -1)), Mul(-1, x))
>>> x - y == nr.Add(x, nr.Mul(nr.NegativeOne, y))
True

```

## Numbers

The numbers are Python `int`s, because `nary/kinds.py` says so:

```python
NumberKind = declare_kind("NumberKind", literals=int)
BoolKind = declare_kind("BoolKind")
```

Calling `NumberKind` with an `int` makes a literal, a leaf that holds the
value and prints as its `repr`. An `int` passed where a `NumberKind` is
expected, to a function or an operator, becomes one, on either side of an
operator. Nothing is computed: `x - 1` is not folded, and `2 + 3` of two
literals stays a sum.

```python
>>> three = nr.NumberKind(3)
>>> three, three.is_literal, three.value, three.kind
(3, True, 3, NumberKind)
>>> nr.sin(1), x + 1, 2 * x, 1 < x
(sin(1), Add(x, 1), Mul(2, x), Gt(x, 1))
>>> x - 1, 1 / x
(Add(x, Mul(-1, 1)), Mul(1, Pow(x, -1)))
>>> three + 2
Add(3, 2)
>>> three == 3, nr.sin(3) == nr.sin(three)
(False, True)
>>> nr.NumberKind(True)
Traceback (most recent call last):
    ...
TypeError: NumberKind takes a name (a str) or a literal of type int, got bool: True
>>> x + 1.5
Traceback (most recent call last):
    ...
TypeError: Add expects NumberKind, got float: 1.5

```

- `literals` is a type or a tuple of types, by default none, and
  `kind.literals` is that tuple. A value is accepted only if its exact type
  is one of them, so a `bool` is not an `int` here. A `str` cannot be one,
  since a string names a symbol.
- Two literals are equal when they have the same kind, the same type and
  equal values. A literal is never equal to a symbol or to a Python value.
- A literal is not a symbol, so it is rejected in a `Symbol(kind)`
  position. `BoolKind` declares no literals, so `True` is not converted.
- The compiled module knows no particular type: it holds the value, and
  converts an argument only when the kind of its position accepts it.

## Constants

A constant is a named leaf that stands for one specific thing.
`declare_constant(name, kind)` declares one, of any kind. `nary/constants.py`
declares `pi`, `E` and `I`, and `nary/logic.py` declares `true` and `false`:

```python
pi = declare_constant("pi", NumberKind)
true = declare_constant("true", BoolKind)
```

```python
>>> from nary.logic import And, true
>>> nr.pi, nr.pi.kind, nr.pi.is_constant, nr.pi.head, nr.pi.args
(pi, NumberKind, True, None, ())
>>> nr.sin(nr.pi), 2 * nr.pi, And(x < nr.pi, true)
(sin(pi), Mul(2, pi), And(Lt(x, pi), true))
>>> nr.pi == nr.NumberKind("pi"), nr.pi == nr.declare_constant("pi", nr.NumberKind)
(False, False)
>>> nr.Lambda(nr.pi, x)
Traceback (most recent call last):
    ...
TypeError: Lambda expects a NumberKind symbol, got NumberKind: pi

```

- A constant is equal only to itself. Every `declare_constant(...)` call
  makes a new one, even with a name already used, and it is never equal to
  a symbol of the same name and kind.
- Unlike a symbol, a constant is not accepted in a `Symbol(kind)` position,
  so it cannot be bound by `Lambda`.
- Nothing is known about a constant but its name and kind: `pi` has no
  numeric value and `I ** 2` stays `Pow(I, 2)`.

## Functions

A declared function is an expression: a declared constant whose kind is a
function kind.
`declare_function(name, *inputs, rest=None, returns, names=None)` declares
one.

```python
>>> from nary import BoolKind, FunctionKind, NumberKind, declare_function

>>> cos = declare_function("cos", NumberKind, returns=NumberKind)
>>> Max = declare_function("Max", rest=NumberKind, returns=NumberKind)
>>> Le = declare_function("Le", NumberKind, NumberKind, returns=BoolKind, names=("lhs", "rhs"))

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

>>> At = declare_function("At", f.kind, NumberKind, returns=NumberKind)
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

### Positions that accept only a symbol

`Symbol(kind)` in a leading position of a declaration means that the
position has that kind and accepts only a symbol of it. It is a marker, not
a kind: the function kind is built from the plain kinds, and the declared
function shows the markers in `params`.

```python
>>> from nary import Symbol

>>> Derivative = declare_function("Derivative", NumberKind, Symbol(NumberKind), returns=NumberKind)
>>> Derivative.kind
FunctionKind((NumberKind, NumberKind), NumberKind)
>>> Derivative.params, Derivative.kind.inputs
((NumberKind, Symbol(NumberKind)), (NumberKind, NumberKind))
>>> Derivative(cos(x), x)
Derivative(cos(x), x)
>>> Derivative(x, cos(x))
Traceback (most recent call last):
    ...
TypeError: Derivative expects a NumberKind symbol, got NumberKind: cos(x)

```

The check belongs to the declared function. An unknown function of the same
kind, `Derivative.kind("D")`, accepts any `NumberKind` in both positions.
`rest=` takes a kind, not a marker.

### Lambda

`Lambda(variables, body)` is not built into the compiled module. It is
defined in Python, in `nary/functions.py`, with `declare_function(...)` and
`Symbol(kind)`: for each combination of kinds it declares, once, a function
named `Lambda` that takes the variables, each declared `Symbol(kind)`, then
the body, and returns the function kind from the kinds of the variables to
the kind of the body. A lambda is an application of that function. So it
prints as `Lambda(x, y, body)`, its `head` is that function, and its `args`
are the variables followed by the body. `is_lambda(e)` tells whether `e` is
one.

```python
>>> from nary import Lambda, is_lambda

>>> square = Lambda(x, x * x)
>>> square, square.kind
(Lambda(x, Mul(x, x)), FunctionKind((NumberKind,), NumberKind))
>>> Lambda((x, y), x < y), Lambda((x, y), x < y).kind
(Lambda(x, y, Lt(x, y)), FunctionKind((NumberKind, NumberKind), BoolKind))
>>> is_lambda(square), square.head.params
(True, (Symbol(NumberKind), NumberKind))
>>> square.args[:-1], square.args[-1]
((x,), Mul(x, x))
>>> square(z), At(square, z)               # applying a lambda is inert
(Lambda(x, Mul(x, x))(z), At(Lambda(x, Mul(x, x)), z))
>>> Lambda(x + y, x)
Traceback (most recent call last):
    ...
TypeError: Lambda expects a NumberKind symbol, got NumberKind: Add(x, y)

```

`variables` is one symbol or a tuple of one or more symbols with different
names; a repeated name, whatever the kinds, is a `ValueError`.

### Attributes and equality

- `e.head` is the head expression of an application and `None` otherwise;
  `e.args` is the arguments of an application and `()` otherwise; `e.name`
  is the name of a symbol or declared constant and `None` otherwise.
  `e.is_symbol` is true for a symbol, `e.is_literal` for a literal and
  `e.is_constant` for a declared constant (so also for a declared function
  such as `sin`), and `e.value` is the Python value of a literal and `None`
  otherwise.
  `e.params` is what a declared function was declared with, and `None` for
  any other expression.
- Named arguments such as `eq.lhs` are looked up through the `names` of
  the head of an application. A name that is already an attribute of
  `Expr`, such as `value` or `name`, finds the attribute instead.
- `FunctionKind(inputs, output, rest=None)` takes a tuple of kinds, possibly
  empty, and one kind. The same arguments give the same kind, so function
  kinds are compared by identity like any other. They can nest, and can be
  parameters of kind families. For any other kind, `inputs`, `rest` and
  `output` are `None`.
- Every `declare_function(...)` call makes a new function, even with a name
  and kind already used, and a declared function is equal only to itself.
- Symbols are equal when they have the same kind and name, literals as
  described under Numbers, and applications
  (lambdas among them) when their heads and arguments are equal. Expressions
  of different forms are never equal.

## Kinds

A kind is declared in Python, and adding one needs no change in Rust:

```python
>>> from nary import declare_kind, set_operator

>>> SetKind = declare_kind("SetKind")
>>> Union = declare_function("Union", rest=SetKind, returns=SetKind)
>>> Contains = declare_function("Contains", NumberKind, SetKind, returns=BoolKind)
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

- Calling a kind takes one argument: a name, which makes a symbol, or a
  value of one of the kind's literal types, which makes a literal. Either
  has `args` `()`. Any further argument is a `TypeError`. A node with
  arguments is built only by calling an expression of a function kind
  (directly or through an operator), so every argument of every node is an
  `Expr` that passed the kind check of its head.
- There is one class of expression, `Expr`, whatever the kind. Test the kind
  with `e.kind is NumberKind`. A kind is not a class, so
  `isinstance(e, NumberKind)` is an error, and `Expr` cannot be subclassed.
- A kind lasts for the life of the process, and an expression refers to it
  without reference counting. Building an expression costs the same whatever
  the kind and however many kinds there are.
- Every `declare_kind(...)` call makes a new kind, even with a name already
  used. Declare each kind once, when a module is imported.
- `set_operator(kind, symbol, function)` says what an operator builds when its
  left operand is of that kind. The operator calls the function (an
  expression of a function kind, or a Python function) with the operands,
  and the result must be an `Expr` (anything else is a `TypeError`). A kind
  with nothing set for an operator does
  not support it: `p + q` on two `BoolKind`s is a `TypeError`.

## Parametrised kinds

A kind family is declared with `declare_kind_family(name)`, and calling it
with kinds as parameters gives a kind. Such a kind is like any other: it can
be used in a signature, it has its own operators, and calling it makes a
symbol.

```python
>>> from nary import declare_kind_family

>>> TupleKind = declare_kind_family("TupleKind")              # one or more parameters
>>> MatrixKind = declare_kind_family("MatrixKind", params=1)  # exactly one parameter

>>> Pair = TupleKind(NumberKind, BoolKind)
>>> Pair
TupleKind(NumberKind, BoolKind)
>>> Pair is TupleKind(NumberKind, BoolKind)           # the same kind every time
True
>>> Pair.family, Pair.params
(<kind family TupleKind>, (NumberKind, BoolKind))
>>> TupleKind(MatrixKind(NumberKind), Pair)           # parameters can be parametrised
TupleKind(MatrixKind(NumberKind), TupleKind(NumberKind, BoolKind))

>>> Piece = declare_function("Piece", NumberKind, BoolKind, returns=Pair)
>>> Piece(x, x < y).kind is Pair
True

>>> Matrix = MatrixKind(NumberKind)
>>> MatMul = declare_function("MatMul", rest=Matrix, returns=Matrix)
>>> Trace = declare_function("Trace", Matrix, returns=NumberKind)
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
  with `declare_kind(name)` and for a function kind. A family has `name`, and
  `params`, the number of parameters it takes or `None`.
- Every `declare_kind_family(...)` call makes a new family, even with a name
  already used, and its kinds are different from those of any other family.

## Limitations

- The ten operators (`+`, `-`, `*`, `/`, `**`, unary minus, `<`, `>`, `<=`,
  `>=`) are fixed in Rust. A reflected operator (`1 + x`) works only by
  turning the left operand into a literal of the kind of the right one.
  `set_operator` can be called once for each kind and operator.
- Integers are the only numbers: there are no rationals or floats, and
  `x + 1.5` is a `TypeError`. Nothing is computed with integers, so
  `x - 1` is `Add(x, Mul(-1, 1))` and `2 + 3` of two literals is `Add(2, 3)`.
- A literal is never equal to a Python value: `NumberKind(3) == 3` is
  `False`. A literal of an unhashable type cannot be hashed.
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
- A symbol, a declared constant and an application of a named head to no
  arguments can all print the same: `NumberKind("Add")`, `Add` and `Add()`
  all print as `Add`, though none is equal to another.
