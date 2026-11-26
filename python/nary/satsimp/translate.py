"""SymPy expressions and Q facts to nary, and back.

    >>> import sympy
    >>> from sympy import Q
    >>> x = sympy.Symbol("x")
    >>> from_sympy(sympy.sin(x) / 2 + sympy.pi)
    Add(pi, Mul(Pow(2, -1), sin(x)))
    >>> from_sympy(Q.positive(x) & ~Q.zero(x - 1))
    And(Gt(x, 0), Not(Eq(Add(-1, x), 0)))

What nary lacks is named.

    >>> from_sympy(sympy.cot(x))
    Traceback (most recent call last):
        ...
    nary.satsimp.translate.Untranslatable: function cot
    >>> from_sympy(Q.integer(x))
    Traceback (most recent call last):
        ...
    nary.satsimp.translate.Untranslatable: predicate integer

to_sympy evaluates, so a round trip is SymPy's automatic simplification.

    >>> import nary as nr
    >>> y = nr.NumberKind("y")
    >>> to_sympy(y * y + y), from_sympy(to_sympy(y / y))
    (y**2 + y, 1)
    >>> to_sympy(nr.logic.And(nr.Gt(y, 0), nr.Eq(nr.re(y), y)))
    Q.positive(y) & Q.real(y)

Unevaluated, the numbers of a product still become one Rational, as SymPy writes them.

    >>> with sympy.evaluate(False):
    ...     sympy.srepr(to_sympy(nr.Mul(3, nr.Pow(2, -1), y, nr.Pow(y, 0))))
    "Mul(Rational(3, 2), Pow(Symbol('y'), Integer(0)), Symbol('y'))"
"""

from fractions import Fraction
from math import prod

import sympy
from sympy import Q
from sympy.assumptions.assume import AppliedPredicate
from sympy.core.function import AppliedUndef

import nary as nr
from nary import logic

__all__ = ["Untranslatable", "from_sympy", "head_named", "head_of", "lacking", "to_sympy"]


class Untranslatable(ValueError):
    @property
    def reason(self):
        return self.args[0]


_FUNCTIONS = {
    sympy.Add: nr.Add, sympy.Mul: nr.Mul, sympy.Pow: nr.Pow,
    sympy.sin: nr.sin, sympy.cos: nr.cos, sympy.tan: nr.tan,
    sympy.exp: nr.exp, sympy.log: nr.log, sympy.re: nr.re,
    sympy.sinh: nr.sinh, sympy.cosh: nr.cosh, sympy.tanh: nr.tanh,
    sympy.Abs: nr.Abs, sympy.im: nr.im, sympy.arg: nr.arg, sympy.conjugate: nr.conjugate,
    sympy.sign: nr.sign, sympy.floor: nr.floor, sympy.ceiling: nr.ceiling,
    sympy.And: logic.And, sympy.Or: logic.Or, sympy.Not: logic.Not,
    sympy.Eq: nr.Eq, sympy.Ne: nr.Ne, sympy.Lt: nr.Lt, sympy.Gt: nr.Gt,
    sympy.Le: nr.Le, sympy.Ge: nr.Ge,
}
_NAMED = {cls.__name__: head for cls, head in _FUNCTIONS.items()}
_CONSTANTS = {
    sympy.pi: nr.pi, sympy.E: nr.E, sympy.I: nr.I,
    sympy.true: logic.true, sympy.false: logic.false,
}
_PREDICATES = {
    Q.zero: lambda a: nr.Eq(a, 0),
    Q.nonzero: lambda a: logic.And(nr.Eq(nr.re(a), a), nr.Ne(a, 0)),
    Q.positive: lambda a: nr.Gt(a, 0),
    Q.negative: lambda a: nr.Lt(a, 0),
    Q.nonnegative: lambda a: nr.Ge(a, 0),
    Q.nonpositive: lambda a: nr.Le(a, 0),
    Q.real: lambda a: nr.Eq(nr.re(a), a),
    Q.extended_real: lambda a: nr.Eq(nr.re(a), a),
    Q.extended_positive: lambda a: nr.Gt(a, 0),
    Q.extended_negative: lambda a: nr.Lt(a, 0),
    Q.extended_nonnegative: lambda a: nr.Ge(a, 0),
    Q.extended_nonpositive: lambda a: nr.Le(a, 0),
    Q.finite: lambda a: logic.true,
    Q.commutative: lambda a: logic.true,
    Q.complex: lambda a: logic.true,
    Q.eq: nr.Eq, Q.ne: nr.Ne, Q.lt: nr.Lt, Q.gt: nr.Gt, Q.le: nr.Le, Q.ge: nr.Ge,
}


def _plain(s):
    return set(s.assumptions0) <= {"commutative"} and s.is_commutative


def _class(s):
    return next((c for c in type(s).__mro__ if c in _FUNCTIONS), None)


def head_of(cls):
    return _FUNCTIONS.get(cls)


def head_named(name):
    return _NAMED.get(name)


def _missing(s, wildcards):
    if isinstance(s, sympy.Symbol):
        if type(s) not in (sympy.Symbol, sympy.Dummy):
            return f"pattern symbol {type(s).__name__}"
        return None if _plain(s) else "symbol with assumptions"
    if s.is_Rational or s in _CONSTANTS:
        return None
    if isinstance(s, AppliedPredicate):
        return None if s.function in _PREDICATES else f"predicate {s.function.name}"
    if isinstance(s, AppliedUndef):
        return None if wildcards else "undefined function"
    if _class(s) is not None:
        return None
    return f"{'number' if s.is_number and not s.args else 'function'} {type(s).__name__}"


def lacking(s, wildcards=False):
    s = sympy.sympify(s)
    found = {_missing(s, wildcards)} - {None}
    for a in (s.arguments if isinstance(s, AppliedPredicate) else s.args):
        found |= lacking(a, wildcards)
    return found


def from_sympy(s, wildcards=False):
    s = sympy.sympify(s)
    reason = _missing(s, wildcards)
    if reason is not None:
        raise Untranslatable(reason)
    if isinstance(s, sympy.Symbol):
        return nr.NumberKind(s.name)
    if s.is_Integer:
        return nr.NumberKind(int(s))
    if s.is_Rational:
        inverse = nr.Pow(nr.NumberKind(int(s.q)), -1)
        return inverse if s.p == 1 else nr.Mul(int(s.p), inverse)
    if s in _CONSTANTS:
        return _CONSTANTS[s]
    if isinstance(s, AppliedPredicate):
        return _PREDICATES[s.function](*(from_sympy(a, wildcards) for a in s.arguments))
    if isinstance(s, AppliedUndef):
        head = nr.FunctionKind((nr.NumberKind,) * len(s.args), nr.NumberKind)(s.func.__name__)
    else:
        head = _FUNCTIONS[_class(s)]
    return head(*(from_sympy(a, wildcards) for a in s.args))


_INVERSE_FUNCTIONS = {v: k for k, v in _FUNCTIONS.items()}
_INVERSE_CONSTANTS = {v: k for k, v in _CONSTANTS.items()}
_SIGNS = {nr.Eq: Q.zero, nr.Gt: Q.positive, nr.Lt: Q.negative, nr.Ge: Q.nonnegative,
          nr.Le: Q.nonpositive}
_FLIPPED = {nr.Eq: nr.Eq, nr.Ne: nr.Ne, nr.Gt: nr.Lt, nr.Lt: nr.Gt, nr.Ge: nr.Le, nr.Le: nr.Ge}
_RELATIONS = {nr.Eq: Q.eq, nr.Gt: Q.gt, nr.Lt: Q.lt, nr.Ge: Q.ge, nr.Le: Q.le}


def _relation(head, a, b):
    zero = nr.NumberKind(0)
    if a == zero and b != zero:
        return _relation(_FLIPPED[head], b, a)
    if head == nr.Ne:
        return ~_relation(nr.Eq, a, b)
    if head == nr.Eq and a == nr.re(b):
        return Q.real(to_sympy(b))
    if b == zero:
        return _SIGNS[head](to_sympy(a))
    a, b = to_sympy(a), to_sympy(b)
    if head == nr.Eq:
        return Q.eq(a, b)
    return sympy.And(_RELATIONS[head](a, b), *(Q.real(s) for s in (a, b) if s.free_symbols))


def _number(e):
    if e.is_literal and e.kind is nr.NumberKind:
        return Fraction(e.value)
    if e.head == nr.Pow and e.args[1] == nr.NumberKind(-1) and e.args[0].is_literal:
        return 1 / Fraction(e.args[0].value) if e.args[0].value else None
    return None


def _rational(q):
    return sympy.Rational(q.numerator, q.denominator)


def to_sympy(e):
    if _number(e) is not None:
        return _rational(_number(e))
    if e.head == nr.Mul:
        numbers = [a for a in e.args if _number(a) is not None]
        rest = [to_sympy(a) for a in e.args if _number(a) is None]
        q = prod(map(_number, numbers), start=Fraction(1))
        return sympy.Mul(*([_rational(q)] if q != 1 or not rest else []), *rest)
    if e.is_symbol:
        if e.kind is not nr.NumberKind:
            raise Untranslatable(f"symbol of {e.kind!r}")
        return sympy.Symbol(e.name)
    if e.is_constant and e in _INVERSE_CONSTANTS:
        return _INVERSE_CONSTANTS[e]
    if e.head in _FLIPPED:
        return _relation(e.head, *e.args)
    head = _INVERSE_FUNCTIONS.get(e.head)
    if head is None:
        raise Untranslatable(f"nary {e.head if e.head is not None else e!r}")
    return head(*map(to_sympy, e.args))
