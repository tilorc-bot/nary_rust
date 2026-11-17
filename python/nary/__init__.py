"""Typed, inert expression trees.

The compiled module ``nary._core`` provides ``Expr``, ``kind``,
``kind_family``, ``function`` and ``set_operator``, and knows nothing about
any particular kind or function. The kinds are declared in ``nary.kinds``,
and each function is declared in one of the other modules of this package
with a ``function(...)`` call. A declaration is only data; calling the
function still runs entirely in Rust.

    import nary as nr

Everything a module of the package lists in its ``__all__`` is re-exported
here, so a new name only needs adding to that module.
"""

from . import arithmetic, elementary, kinds, relational
from ._core import (
    Expr,
    Function,
    Kind,
    KindFamily,
    Symbol,
    function,
    kind,
    kind_family,
    set_operator,
)
from .arithmetic import *  # noqa: F403
from .elementary import *  # noqa: F403
from .kinds import *  # noqa: F403
from .relational import *  # noqa: F403

__all__ = [
    # the declaration machinery, from the compiled module
    "Expr", "Function", "Kind", "KindFamily", "Symbol", "function", "kind",
    "kind_family", "set_operator",
    # the kinds and functions declared in the modules of this package
    *kinds.__all__,
    *arithmetic.__all__,
    *elementary.__all__,
    *relational.__all__,
]
