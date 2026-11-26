"""An implication says that its conclusion holds where all its premises hold.

    >>> from nary import Gt, Mul, NumberKind
    >>> from nary.implications import Implication
    >>> a, b = NumberKind("a"), NumberKind("b")
    >>> Implication(Gt(a * b, 0), Gt(a, 0), Gt(b, 0))
    Implication(Gt(Mul(a, b), 0), Gt(a, 0), Gt(b, 0))

Every symbol of a premise must be in the conclusion.

    >>> Implication(Gt(a * a, 0), Gt(b, 0))
    Traceback (most recent call last):
        ...
    ValueError: every symbol of an implication must be in its conclusion, but b is in a premise only
"""

from ._core import Expr
from .arithmetic import Mul, Pow
from .constants import E, I, pi
from .elementary import cos, exp, log, sin, tan
from .kinds import BoolKind, NumberKind
from .relational import Eq, Ge, Gt, Le, Lt, Ne, re

__all__ = ["Implication", "implications"]


def _symbols(e):
    if e.is_symbol:
        return {e}
    return set().union(*(_symbols(arg) for arg in e.args))


class Implication:
    __slots__ = ("conclusion", "premises")

    def __init__(self, conclusion, *premises):
        for c in (conclusion, *premises):
            if not (isinstance(c, Expr) and c.kind is BoolKind):
                raise TypeError(f"an implication relates BoolKind expressions, got {c!r}")
        for premise in premises:
            for symbol in _symbols(premise) - _symbols(conclusion):
                raise ValueError(
                    f"every symbol of an implication must be in its conclusion, "
                    f"but {symbol!r} is in a premise only"
                )
        self.conclusion, self.premises = conclusion, premises

    def __repr__(self):
        return f"Implication({', '.join(map(repr, (self.conclusion, *self.premises)))})"


a, b = NumberKind("a"), NumberKind("b")

implications = [
    Implication(Eq(re(pi), pi)),
    Implication(Eq(re(E), E)),
    Implication(Gt(pi, 3)),
    Implication(Lt(pi, 4)),
    Implication(Gt(E, 2)),
    Implication(Lt(E, 3)),
    Implication(Ne(I, 0)),
    Implication(Eq(re(re(a)), re(a)), Eq(a, a)),

    Implication(Eq(re(Mul(a, b)), Mul(a, b)), Eq(re(a), a), Eq(re(b), b)),
    Implication(Gt(Mul(a, b), 0), Gt(a, 0), Gt(b, 0)),
    Implication(Gt(Mul(a, b), 0), Lt(a, 0), Lt(b, 0)),
    Implication(Lt(Mul(a, b), 0), Gt(a, 0), Lt(b, 0)),
    Implication(Lt(Mul(a, b), 0), Lt(a, 0), Gt(b, 0)),
    Implication(Ge(Mul(a, b), 0), Ge(a, 0), Ge(b, 0)),
    Implication(Ge(Mul(a, b), 0), Le(a, 0), Le(b, 0)),
    Implication(Le(Mul(a, b), 0), Ge(a, 0), Le(b, 0)),
    Implication(Le(Mul(a, b), 0), Le(a, 0), Ge(b, 0)),
    Implication(Ne(Mul(a, b), 0), Ne(a, 0), Ne(b, 0)),

    Implication(Eq(re(Pow(a, b)), Pow(a, b)), Gt(a, 0), Eq(re(b), b)),
    Implication(Eq(re(Pow(a, b)), Pow(a, b)), Ge(a, 0), Gt(b, 0)),
    Implication(Eq(re(Pow(a, 2)), Pow(a, 2)), Eq(re(a), a)),
    Implication(Eq(re(Pow(a, -1)), Pow(a, -1)), Eq(re(a), a), Ne(a, 0)),
    Implication(Gt(Pow(a, b), 0), Gt(a, 0), Eq(re(b), b)),
    Implication(Ge(Pow(a, b), 0), Ge(a, 0), Gt(b, 0)),
    Implication(Ge(Pow(a, 2), 0), Eq(re(a), a)),
    Implication(Gt(Pow(a, 2), 0), Eq(re(a), a), Ne(a, 0)),
    Implication(Lt(Pow(a, -1), 0), Lt(a, 0)),
    Implication(Ne(Pow(a, b), 0), Ne(a, 0), Eq(b, b)),

    Implication(Eq(re(exp(a)), exp(a)), Eq(re(a), a)),
    Implication(Gt(exp(a), 0), Eq(re(a), a)),
    Implication(Ne(exp(a), 0), Eq(a, a)),
    Implication(Gt(exp(a), 1), Gt(a, 0)),
    Implication(Lt(exp(a), 1), Lt(a, 0)),

    Implication(Eq(re(log(a)), log(a)), Gt(a, 0)),
    Implication(Gt(log(a), 0), Gt(a, 1)),
    Implication(Lt(log(a), 0), Gt(a, 0), Lt(a, 1)),
    Implication(Ne(log(a), 0), Ne(a, 0), Ne(a, 1)),

    Implication(Eq(re(sin(a)), sin(a)), Eq(re(a), a)),
    Implication(Ge(sin(a), -1), Eq(re(a), a)),
    Implication(Le(sin(a), 1), Eq(re(a), a)),
    Implication(Gt(sin(a), 0), Gt(a, 0), Lt(a, pi)),
    Implication(Eq(re(cos(a)), cos(a)), Eq(re(a), a)),
    Implication(Ge(cos(a), -1), Eq(re(a), a)),
    Implication(Le(cos(a), 1), Eq(re(a), a)),
    Implication(Eq(re(tan(a)), tan(a)), Eq(re(a), a), Ne(cos(a), 0)),
]
