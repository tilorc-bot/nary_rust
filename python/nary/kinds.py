"""The kinds and the kind families.

A kind is declared with ``kind(name)`` and a family of kinds with
``kind_family(name)``. Adding a kind is adding a line here; nothing in Rust
changes. Every expression is an ``Expr``, and ``e.kind`` is a kind:
``NumberKind``, or a kind made by a family, such as ``SetKind(NumberKind)``.
"""

from ._core import kind, kind_family, set_integer_kind

NumberKind = kind("NumberKind")
BoolKind = kind("BoolKind")

# A set of elements of one kind: SetKind(NumberKind) is a set of numbers.
# Only sets of numbers have functions (in sets.py).
SetKind = kind_family("SetKind", params=1)

# A matrix with entries of one kind: MatrixKind(NumberKind) is a matrix of
# numbers. The kind does not record the shape. Only matrices of numbers have
# functions (in matrices.py).
MatrixKind = kind_family("MatrixKind", params=1)

# An Integer is a NumberKind, and so is a Python int given where a NumberKind
# is expected.
set_integer_kind(NumberKind)

# TODO: there is no tuple kind and no function kind. See calculus.py for what
# is left out because of that.
