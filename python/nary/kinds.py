from ._core import declare_kind

__all__ = ["BoolKind", "NumberKind"]

NumberKind = declare_kind("NumberKind", literals=int)
BoolKind = declare_kind("BoolKind")
