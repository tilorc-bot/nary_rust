"""SymPy's automatic evaluation as a canonical form, and satassume's ask on Q facts as decide, for comparison.

    >>> import nary as nr
    >>> from nary.satsimp.prove import prover
    >>> x = nr.NumberKind("x")
    >>> round_trip(x / x), round_trip(nr.logic.Not(nr.BoolKind("p")))
    (1, Not(p))
    >>> known = prover(nr.Gt(x, 1), decide=ask)
    >>> known(nr.Ne(x, 0)), known(nr.Lt(x, 0)), known(nr.Eq(nr.re(x), x))
    (True, False, True)
"""

from functools import cache

import sympy
from satassume.sympy_api import ask as satassume_ask

from .translate import Untranslatable, from_sympy, to_sympy

__all__ = ["ask", "round_trip"]


def round_trip(e, known=()):
    try:
        return from_sympy(to_sympy(e))
    except Untranslatable:
        return e


@cache
def _facts(known):
    return sympy.And(*map(to_sympy, known))


def ask(condition, known):
    try:
        question, facts = to_sympy(condition), _facts(known)
    except Untranslatable:
        return False
    if question in (sympy.true, sympy.false):
        return question is sympy.true
    try:
        return satassume_ask(question, facts) is True
    except (ValueError, TypeError):
        return False
