"""The kinds.

A kind is declared with ``kind(name)``. Adding a kind is adding a line here;
nothing in Rust changes. Every expression is an ``Expr``, and ``e.kind`` is
one of these objects.
"""

from ._core import kind

NumberKind = kind("NumberKind")
BoolKind = kind("BoolKind")
