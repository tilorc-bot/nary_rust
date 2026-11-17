# nary_rust

Typed, inert expression trees for Python, with the checking and node
construction written in Rust (PyO3).

- There is one class per kind of expression: `NumberKind` and `Bool`.
- A function declares the kinds it accepts and the kind it returns. The result
  is always an instance of the declared kind; nothing is inferred from the
  arguments.
- A function can take any number of arguments of one kind (`rest=`).
- Expressions are inert: nothing is flattened, reordered or evaluated when an
  expression is built.

## Layout

| File | What it is |
|---|---|
| `src/lib.rs` | The compiled module `nary_rust`: `Expr`, `NumberKind`, `Bool`, `Function`, `function`, `set_operator`. It defines no particular function. |
| `nary_rs.py` | Declares `Add`, `Mul`, `Pow`, `sin`, `Lt` and `Eq` with `function(...)`, and sets which function each operator builds. This is the module to import. |

## Build

Needs a Rust toolchain and [uv](https://docs.astral.sh/uv/).

    uvx maturin build -r -i python3

The wheel is written to `target/wheels/`. It contains only the compiled
module; `nary_rs.py` is used from this directory.

## Use

    uv run --no-project --with target/wheels/nary_rust-*.whl python

```python
>>> import nary_rs as nr
>>> x, y, z = (nr.NumberKind(n) for n in "xyz")

>>> nr.Add(x, y, z)                  # any number of arguments
Add(x, y, z)
>>> x + y + z                        # operators build two-argument nodes
Add(Add(x, y), z)
>>> nr.sin(x) * y < z                # a comparison is a Bool
Lt(Mul(sin(x), y), z)

>>> eq = nr.Eq(x + y, z)             # named arguments
>>> eq.lhs, eq.rhs
(Add(x, y), z)

>>> nr.sin(x < y)
TypeError: sin expects NumberKind, got Bool: Lt(x, y)
>>> nr.Pow(x, y, z)
TypeError: Pow takes 2 arguments, got 3
```

Declaring a function:

```python
from nary_rust import Bool, NumberKind, function

cos = function("cos", NumberKind, returns=NumberKind)
Max = function("Max", rest=NumberKind, returns=NumberKind)
Le = function("Le", NumberKind, NumberKind, returns=Bool, names=("lhs", "rhs"))
```

## Limitations

- The two kinds and the three operators (`+`, `*`, `<`) are fixed in Rust.
  `set_operator` can be called once per operator.
- `==` compares structure and returns a Python `bool`; it does not build an
  `Eq`. `x + y + z` is not equal to `Add(x, y, z)`.
- Equal expressions are not shared, so equality walks both trees.
- Equality ignores the kind: `NumberKind("p") == Bool("p")`.
