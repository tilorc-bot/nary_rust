"""The kinds.

A kind is declared with ``declare_kind(name)``. Adding a kind is adding a
line here; nothing in Rust changes. Every expression is an ``Expr``, and
``e.kind`` is one of these objects.

``literals=int`` says that a Python ``int`` is a literal of ``NumberKind``:
``NumberKind(3)`` makes one, and an ``int`` passed where a ``NumberKind`` is
expected, as in ``sin(3)`` or ``x + 1``, becomes one. ``BoolKind`` accepts
no literals, so ``True`` is not converted.
"""

from ._core import declare_kind

__all__ = ["BoolKind", "NumberKind"]

NumberKind = declare_kind("NumberKind", literals=int)
BoolKind = declare_kind("BoolKind")
