"""simplify rewrites with the rules on top of autosimp at every node.

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

Known facts are given as a list of conditions.

    >>> simplify(log(exp(x))), simplify(log(exp(x)), [Eq(re(x), x)])
    (log(exp(x)), x)
    >>> simplify(x / x), simplify(x / x, [Ne(x, 0)])
    (Pow(x, 0), 1)
"""

from . import elementary_rules, logic_rules
from .calculus import Derivative
from .differentiation import derivative
from .functions import Lambda
from .autosimp import node
from .rewriting import beta, holds, rewrite

__all__ = ["rules", "simplify"]

rules = elementary_rules.rules + logic_rules.rules


def simplify(e, known=None):
    from .strategies import apply
    return apply("simplify", e, known)


def _normal(e, known, facts=frozenset()):
    reduced = beta(e)
    if reduced == e and e.head is not None and e.head.head == Derivative:
        reduced = _differentiate(e, known)
    return reduced if reduced != e else node(e.head, list(e.args), facts)


def _differentiate(e, known):
    found = derivative(e.head.args[0])
    if found is None:
        return e
    f, conditions = found
    point = dict(zip(f.args[:-1], e.args))
    if not all(holds(_at(c, point), known) for c in conditions):
        return e
    return beta(f(*e.args))


def _at(c, point):
    return beta(Lambda(*point, c)(*point.values()))
