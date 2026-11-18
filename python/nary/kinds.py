"""The kinds.

A kind is declared with ``declare_kind(name)``. Adding a kind is adding a
line here; nothing in Rust changes. Every expression is an ``Expr``, and
``e.kind`` is one of these objects.

``set_integer_kind(NumberKind)`` says that integers are ``NumberKind``s:
``Integer(3)`` is one, and a Python ``int`` given where a ``NumberKind`` is
expected is converted to one.
"""

from ._core import declare_kind, set_integer_kind

__all__ = ["BoolKind", "NumberKind"]

NumberKind = declare_kind("NumberKind")
set_integer_kind(NumberKind)
BoolKind = declare_kind("BoolKind")
