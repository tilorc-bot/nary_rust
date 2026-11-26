"""simplify rewrites with every rule list and the normal form.

    >>> from nary import Eq, Ne, NumberKind, exp, log, re, sin
    >>> from nary.logic import And, Not, BoolKind, true
    >>> from nary.simplify import simplify
    >>> x, y, p = NumberKind("x"), NumberKind("y"), BoolKind("p")
    >>> simplify(NumberKind(2) + 3), simplify(x + x + x), simplify(2 * x + 3 * x)
    (5, Mul(3, x), Mul(5, x))
    >>> simplify(x * x), simplify(x**2 * x), simplify(y + x) == simplify(x + y), simplify(-(-x))
    (Pow(x, 2), Pow(x, 3), True, x)
    >>> simplify(sin(0)), simplify(And(p, true)), simplify(Not(Not(p))), simplify(Eq(x, x))
    (0, p, p, true)

Known facts are given as a list of conditions or as a function.

    >>> simplify(log(exp(x))), simplify(log(exp(x)), [Eq(re(x), x)])
    (log(exp(x)), x)
    >>> simplify(x / x), simplify(x / x, [Ne(x, 0)]), simplify(x / x, lambda c: c == Ne(x, 0))
    (Mul(Pow(x, -1), x), 1, 1)
"""

from . import arithmetic_rules, elementary_rules, logic_rules
from .normal import normal
from .rewriting import beta, rewrite

__all__ = ["rules", "simplify"]

rules = arithmetic_rules.rules + elementary_rules.rules + logic_rules.rules


def simplify(e, known=None):
    if known is not None and not callable(known):
        known = frozenset(known).__contains__
    return rewrite(e, rules, known, _normal)


def _normal(e, known):
    reduced = beta(e)
    return reduced if reduced != e else normal(e, known)
