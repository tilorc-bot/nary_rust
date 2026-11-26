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
from .logic_rules import simplify_logic, to_nnf
from .normal import n_is_an_integer
from .relational import Eq, Gt, Le, Lt, Ne, re
from .rules import rule
from .rewriting import rewrite
from .simplify import _normal, rules

__all__ = ["STRATEGIES", "apply"]

a, b, c, d, n = (NumberKind(s) for s in "abcdn")
cs, ds = Many(NumberKind)("cs"), Many(NumberKind)("ds")

log_rules = [
    rule(log(Mul(a, b, cs)), log(a) + log(Mul(b, cs)),
         when=Gt(a, 0), name="expand_log_positive_factor"),
    rule(log(Mul(a, b, cs)), log(-a) + log(-b) + log(Mul(cs)), when=And(Lt(a, 0), Lt(b, 0)),
         name="expand_log_negative_pair"),
    rule(log(Mul(a, b, cs)), log(-a) + log(-Mul(b, cs)), when=And(Lt(a, 0), Ne(a, -1)),
         name="expand_log_negative_factor"),
    rule(log(a**b), b * log(a),
         when=And(Eq(re(b), b), Gt(b, -1), Le(b, 1)), name="expand_log_root"),
]
expand = [
    rule(a * Add(b, c, cs), a * b + a * Add(c, cs), name="expand_distribute"),
    rule(Add(a, b, cs) ** n, a * Add(a, b, cs) ** (n - 1) + Add(b, cs) * Add(a, b, cs) ** (n - 1),
         when=And(n_is_an_integer, Gt(n, 1)), name="expand_power_of_sum"),
    rule(Add(a, b, cs) ** n, (Add(a, b, cs) ** -n) ** -1, when=And(n_is_an_integer, Lt(n, -1)),
         name="expand_reciprocal_power_of_sum"),
    rule(exp(Add(a, b, cs)), exp(a) * exp(Add(b, cs)), name="expand_exp_sum"),
    *log_rules,
]
expand_log = log_rules
logcombine = [
    rule(c * log(a), log(a**c), when=And(Gt(a, 0), Gt(c, 0)), name="logcombine_coefficient"),
    rule(c * log(a), -log(a ** -c), when=And(Gt(a, 0), Lt(c, 0), Ne(c, -1)),
         name="logcombine_negative_coefficient"),
    rule(log(a**c), -log(a ** -c), when=And(Gt(a, 0), Lt(c, 0)), name="logcombine_negative_power"),
    rule(log(a) + log(b), log(a * b), when=And(Gt(a, 0), Gt(b, 0)), name="logcombine_sum"),
    rule(log(a) - log(b), log(a / b), when=And(Gt(a, 0), Gt(b, 0)), name="logcombine_difference"),
    rule(-log(a) - log(b), -log(a * b),
         when=And(Gt(a, 0), Gt(b, 0)), name="logcombine_negative_sum"),
]
expand_trig = [
    rule(sin(Add(a, b, cs)), sin(a) * cos(Add(b, cs)) + sin(Add(b, cs)) * cos(a),
         name="expand_trig_sin_sum"),
    rule(cos(Add(a, b, cs)), cos(a) * cos(Add(b, cs)) - sin(a) * sin(Add(b, cs)),
         name="expand_trig_cos_sum"),
    rule(sin(2 * a), Mul(2, sin(a), cos(a)), name="expand_trig_sin_double"),
    rule(cos(2 * a), 2 * cos(a) ** 2 - 1, name="expand_trig_cos_double"),
    rule(sin(3 * a), 3 * sin(a) - 4 * sin(a) ** 3, name="expand_trig_sin_triple"),
    rule(cos(3 * a), 4 * cos(a) ** 3 - 3 * cos(a), name="expand_trig_cos_triple"),
]
trigsimp = [
    rule(sin(a) * cos(a), sin(2 * a) / 2, name="trigsimp_sin_double"),
    rule(cos(a) ** 2 - sin(a) ** 2, cos(2 * a), name="trigsimp_cos_double"),
    rule(Add(Mul(2, cos(a) ** 2), -1), cos(2 * a), name="trigsimp_cos_double_cos"),
    rule(Add(1, Mul(-2, sin(a) ** 2)), cos(2 * a), name="trigsimp_cos_double_sin"),
    rule(tan(a) ** 2 + 1, cos(a) ** -2, name="trigsimp_tan_squared"),
    rule(Add(cos(a) ** -2, -1), tan(a) ** 2, name="trigsimp_secant_squared"),
    rule(sin(a) ** n * cos(a) ** -n, tan(a) ** n,
         when=And(n_is_an_integer, Gt(n, 0)), name="trigsimp_tan_power"),
    rule(sin(a) * cos(b) + sin(b) * cos(a), sin(a + b), name="trigsimp_sin_sum"),
    rule(cos(a) * cos(b) + Mul(-1, sin(a), sin(b)), cos(a + b), name="trigsimp_cos_sum"),
]
together = [
    rule(Mul(b**n, cs) + Mul(b**n, ds), (Mul(cs) + Mul(ds)) * b**n,
         when=Lt(n, 0), name="together_same_denominator"),
    rule(Mul(b**n, cs) + c, (Mul(cs) + b**-n * c) * b**n,
         when=Lt(n, 0), name="together_denominator"),
]
powsimp = [
    rule(a**c * a**d, a ** (c + d), when=Gt(a, 0), name="powsimp_positive_base"),
    rule(exp(a) * exp(b), exp(a + b), name="powsimp_exp"),
]

STRATEGIES = {
    "expand": expand, "expand_log": expand_log, "logcombine": logcombine,
    "expand_trig": expand_trig, "trigsimp": trigsimp, "together": together, "powsimp": powsimp,
    "simplify_logic": simplify_logic, "to_nnf": to_nnf,
}


REPLACED = {"logcombine": {"log_pow"}}


def apply(name, e, known=None):
    if known is not None and not callable(known):
        known = frozenset(known).__contains__
    kept = [r for r in rules if r.name not in REPLACED.get(name, ())]
    return rewrite(e, kept + STRATEGIES[name], known, _normal)

