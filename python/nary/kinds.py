from fractions import Fraction

from ._core import Many, declare_kind

__all__ = ["BoolKind", "Many", "NumberKind"]

NumberKind = declare_kind("NumberKind", literals=(int, Fraction))
BoolKind = declare_kind("BoolKind")
