"""The kinds.

A kind is declared with ``declare_kind(name)``. Adding a kind is adding a
line here; nothing in Rust changes. Every expression is an ``Expr``, and
``e.kind`` is one of these objects.
"""

from ._core import declare_kind

__all__ = ["BoolKind", "NumberKind"]

NumberKind = declare_kind("NumberKind")
BoolKind = declare_kind("BoolKind")
