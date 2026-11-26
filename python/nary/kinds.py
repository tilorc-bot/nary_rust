from ._core import Many, declare_kind

__all__ = ["BoolKind", "Many", "NumberKind"]

NumberKind = declare_kind("NumberKind", literals=int)
BoolKind = declare_kind("BoolKind")
