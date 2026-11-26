"""SymPy's opt-in functions as extra rules on top of simplify.

    >>> from nary import Gt, NumberKind, cos, log, sin, tan
    >>> from nary.strategies import apply
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> apply("expand_log", log(x * y), [Gt(x, 0), Gt(y, 0)])
    Add(log(x), log(y))
    >>> apply("logcombine", log(x) + log(y), [Gt(x, 0), Gt(y, 0)])
    log(Mul(x, y))
    >>> apply("expand_trig", sin(2 * x)), apply("trigsimp", 2 * sin(x) * cos(x))
    (Mul(2, cos(x), sin(x)), sin(Mul(2, x)))
    >>> apply("trigsimp", tan(x) ** 2 + 1)
    Pow(cos(x), -2)
"""

from .arithmetic import Add, Mul
from .elementary import cos, exp, log, sin, tan
from .kinds import Many, NumberKind
from .logic import And
from .relational import Gt
from .rules import rule
from .rewriting import rewrite
from .simplify import _normal, rules

__all__ = ["STRATEGIES", "apply"]

a, b, c, d = (NumberKind(s) for s in "abcd")
cs = Many(NumberKind)("cs")

expand = [
    rule(a * Add(b, c, cs), a * b + a * Add(c, cs), name="expand_distribute"),
    rule((a + b) ** 2, a**2 + 2 * a * b + b**2, name="expand_square"),
]
expand_log = [
    rule(log(a * b), log(a) + log(b), when=And(Gt(a, 0), Gt(b, 0)), name="expand_log_product"),
]
logcombine = [
    rule(log(a) + log(b), log(a * b), when=And(Gt(a, 0), Gt(b, 0)), name="logcombine_sum"),
]
expand_trig = [
    rule(sin(2 * a), Mul(2, sin(a), cos(a)), name="expand_trig_sin_double"),
    rule(cos(2 * a), cos(a) ** 2 - sin(a) ** 2, name="expand_trig_cos_double"),
]
trigsimp = [
    rule(Mul(2, sin(a), cos(a)), sin(2 * a), name="trigsimp_sin_double"),
    rule(cos(a) ** 2 - sin(a) ** 2, cos(2 * a), name="trigsimp_cos_double"),
    rule(tan(a) ** 2 + 1, cos(a) ** -2, name="trigsimp_tan_squared"),
]
together = [
    rule(a / b + c / d, (a * d + b * c) / (b * d), name="together_fractions"),
]
powsimp = [
    rule(a**c * a**d, a ** (c + d), when=Gt(a, 0), name="powsimp_positive_base"),
    rule(exp(a) * exp(b), exp(a + b), name="powsimp_exp"),
]

STRATEGIES = {
    "expand": expand, "expand_log": expand_log, "logcombine": logcombine,
    "expand_trig": expand_trig, "trigsimp": trigsimp, "together": together, "powsimp": powsimp,
}


def apply(name, e, known=None):
    if known is not None and not callable(known):
        known = frozenset(known).__contains__
    return rewrite(e, rules + STRATEGIES[name], known, _normal)

