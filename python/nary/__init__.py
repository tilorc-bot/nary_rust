"""Typed, inert expression trees.

The compiled module ``nary._core`` provides ``Expr``, ``declare_kind``,
``declare_kind_family``, ``FunctionKind``, ``declare_function``,
``declare_constant``, ``Symbol`` and ``set_operator``, and knows nothing about
any particular kind, function or constant other than function kinds. The
kinds are declared in ``nary.kinds``, and each function is declared in one of
the other modules of this package with a ``declare_function(...)`` call,
which makes an expression of a function kind. The constants ``pi``, ``E``
and ``I`` are declared in ``nary.constants`` with ``declare_constant(...)``.
``Lambda`` is defined in ``nary.functions`` on top of ``declare_function``
and ``Symbol``. A declaration is only data; calling a function still runs
entirely in Rust.

    import nary as nr

Everything a module of the package lists in its ``__all__`` is re-exported
here, so a new name only needs adding to that module.
"""

from . import arithmetic, constants, elementary, functions, kinds, relational
from ._core import (
    Expr,
    FunctionKind,
    Kind,
    KindFamily,
    Symbol,
    declare_constant,
    declare_function,
    declare_kind,
    declare_kind_family,
    set_operator,
)
from .arithmetic import *  # noqa: F403
from .constants import *  # noqa: F403
from .elementary import *  # noqa: F403
from .functions import *  # noqa: F403
from .kinds import *  # noqa: F403
from .relational import *  # noqa: F403

__all__ = [
    # the declaration machinery, from the compiled module
    "Expr", "FunctionKind", "Kind", "KindFamily", "Symbol",
    "declare_constant", "declare_function", "declare_kind", "declare_kind_family",
    "set_operator",
    # the kinds, functions and constants declared in the modules of this package
    *kinds.__all__,
    *arithmetic.__all__,
    *constants.__all__,
    *elementary.__all__,
    *functions.__all__,
    *relational.__all__,
]
