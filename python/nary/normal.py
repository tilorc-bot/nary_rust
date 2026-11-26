"""normal collects terms and factors and sorts the arguments of Add and Mul.

    >>> from nary import Add, I, Lt, Mul, Ne, NumberKind, Pow, log, re
    >>> from nary.normal import normal
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> normal(Add(x, x, Mul(2, x), 1)), normal(Mul(y, x, 2, x)), normal(Mul(2, Add(x, y)))
    (Add(1, Mul(4, x)), Mul(2, Pow(x, 2), y), Add(Mul(2, x), Mul(2, y)))

A step that could change where an expression has a value needs a condition.

    >>> normal(Add(log(y), Mul(-1, log(y)))), normal(Mul(x, Pow(x, -1)))
    (Mul(0, log(y)), Mul(Pow(x, -1), x))
    >>> normal(Mul(x, Pow(x, -1)), lambda c: c == Ne(x, 0))
    1

Comparisons and real parts of numbers are evaluated.

    >>> normal(Lt(1, Pow(2, -1))), normal(Lt(I, 2)), normal(re(Add(Pow(2, -1), I)))
    (false, Lt(I, 2), Pow(2, -1))
"""

from .arithmetic import Add, Mul, Pow
from .constants import I, pi
from .elementary import exp
from .kinds import NumberKind
from .logic import And
from .numbers import Number, _mul, compare, power, real_part, to_expr, value
from .relational import Eq, Ge, Gt, Le, Lt, Ne, re
from .rewriting import has_a_value, holds
from .rules import rule

__all__ = ["laws", "normal", "order_key"]

a, b, c, n = NumberKind("a"), NumberKind("b"), NumberKind("c"), NumberKind("n")
x, y = NumberKind("x"), NumberKind("y")
n_is_an_integer = Eq(exp(2 * pi * I * n), 1)

laws = [
    rule(a * x + b * x, (a + b) * x, name="collect_terms"),
    rule(x + 0, x, name="add_zero"),
    rule(x * 1, x, name="mul_one"),
    rule(x * 0, 0, name="mul_zero"),
    rule(a * (x + y), a * x + a * y, name="distribute"),
    rule(x**a * x**b, x ** (a + b), when=Ne(x, 0), name="collect_powers"),
    rule(x**a * x**b, x ** (a + b), when=And(Gt(re(a), 0), Gt(re(b), 0)),
         name="collect_positive_powers"),
    rule(x**a * x ** (c * a), x ** ((1 + c) * a), when=Gt(c, 0), name="collect_parallel_powers"),
    rule(a**c * b**c, (a * b) ** c, when=And(Gt(a, 0), Gt(b, 0)), name="combine_radicals"),
    rule(b ** (n + x), b**n * b**x, when=Ne(b, 0), name="split_exponent"),
    rule(Pow(0, c * x), Pow(0, x), when=Gt(c, 0), name="zero_base"),
    rule(x**1, x, name="pow_one"),
    rule(x**0, 1, when=Ne(x, 0), name="pow_zero"),
    rule((x * y) ** n, x**n * y**n, when=n_is_an_integer, name="mul_pow_integer"),
    rule((x**a) ** n, x ** (a * n), when=And(n_is_an_integer, Gt(n, 0)),
         name="pow_pow_positive_integer"),
    rule((x**a) ** n, x ** (a * n), when=And(n_is_an_integer, Ne(x, 0)),
         name="pow_pow_integer"),
    rule(exp(a) ** n, exp(n * a), when=n_is_an_integer, name="exp_pow_integer"),
    rule((c * x) ** a, c**a * x**a, when=Gt(c, 0), name="pow_positive_factor"),
]


def normal(e, known=None):
    if e.head is None:
        return e
    if e.head in (Eq, Ne, Lt, Le, Gt, Ge, re):
        values = [value(arg) for arg in e.args]
        if None not in values:
            return to_expr(real_part(*values)) if e.head == re else compare(e.head, *values) or e
    if e.kind is not NumberKind:
        return e
    v = value(e)
    if v is not None:
        return to_expr(v)
    if e.head == Add or e.head == Mul:
        return _collect(e.head, e.args, known)
    if e.head == Pow:
        return _pow(*e.args, known)
    return e


def order_key(e):
    """
    >>> from nary import NumberKind, Pow, sin
    >>> x = NumberKind("x")
    >>> sorted([sin(x), Pow(x, 2), x, Pow(2, -1), NumberKind(3)], key=order_key)
    [Pow(2, -1), 3, x, Pow(x, 2), sin(x)]
    """
    v = value(e) if e.kind is NumberKind else None
    if v is not None:
        return (0, v.re, v.im)
    if e.head == Pow:
        return (1, _atom_key(e.args[0]), order_key(e.args[1]))
    return (1, _atom_key(e), (0, 1, 0))


def _atom_key(e):
    if e.is_literal:
        return (0, repr(e))
    if e.head is None:
        return (1, e.name, e.is_constant, repr(e.kind))
    return (2, order_key(e.head), tuple(order_key(arg) for arg in e.args))


def _collect(head, args, known):
    adding = head == Add
    identity = 0 if adding else 1
    number, groups = Number(identity), {}
    args = _flatten(head, args)
    for arg in args if adding else _flatten(head, _combine_radicals(args, known)):
        v = _coefficient(head, arg)
        if v is not None:
            number = number + v if adding else number * v
        else:
            key, coefficient = (_split_term if adding else _split_factor)(arg)
            groups.setdefault(key, []).append(coefficient)
    joined = []
    for key, coefficients in groups.items():
        for coefficient in _merge(head, key, coefficients, known):
            joined.append(_collect(Mul, [coefficient, key], known) if adding
                          else _pow(key, coefficient, known))
    radicals = [e for e in map(_radical_exponent, joined) if e is not None]
    if not adding and len(set(radicals)) < len(radicals) or any(
            _coefficient(head, j) is not None or j.head == head for j in joined):
        return _collect(head, [to_expr(number), *joined], known)
    joined.sort(key=order_key)
    if not adding:
        if number == 0 and all(has_a_value(j, known) for j in joined):
            return NumberKind(0)
        if number != 1 and number.im == 0 and len(joined) == 1 and joined[0].head == Add:
            return _collect(Add, [_collect(Mul, [to_expr(number), t], known)
                                  for t in joined[0].args], known)
    first = [] if number == identity else _flatten(head, [to_expr(number)])
    result = [*first, *joined]
    if not result:
        return NumberKind(identity)
    return result[0] if len(result) == 1 else head(*result)


def _coefficient(head, e):
    v = value(e)
    return None if head == Mul and v is not None and v.is_sum else v


def _flatten(head, args):
    flat = []
    for arg in args:
        flat.extend(arg.args if arg.head == head else (arg,))
    return flat


def _split_term(t):
    if t.head != Mul:
        return t, NumberKind(1)
    numbers = [f for f in t.args if _is_real(f)]
    rest = [f for f in t.args if not _is_real(f)]
    return _mul(rest), _mul(numbers or [NumberKind(1)])


def _is_real(e):
    v = value(e)
    return v is not None and v.im == 0


def _is_integer(e):
    v = value(e)
    return v is not None and v.is_integer


def _sum(terms):
    return terms[0] if len(terms) == 1 else Add(*terms)


def _split_factor(f):
    return (f.args[0], f.args[1]) if f.head == Pow else (f, NumberKind(1))


def _merge(head, key, coefficients, known):
    if len(coefficients) == 1:
        return coefficients
    if head == Add or _nonzero(key, known):
        return [_collect(Add, coefficients, known)]
    directions = {}
    for e in coefficients:
        directions.setdefault(_direction(e), []).append(e)
    return [_collect(Add, group, known) for group in directions.values()]


def _direction(e):
    v = value(e)
    if v is not None:
        return (0,) if v.re > 0 else (1,) if v.im == 0 and v.re < 0 else (2, e)
    rest, c = _split_term(e)
    return (2, e) if value(c) == 0 else (3, rest, value(c).re > 0)


def _radical_exponent(f):
    if f.head == Pow and _is_real(f.args[0]) and value(f.args[0]).re > 0 and _is_real(f.args[1]):
        return value(f.args[1])
    return None


def _combine_radicals(factors, known):
    others, radicals = [], {}
    for f in factors:
        e = _radical_exponent(f)
        if e is None:
            others.append(f)
        else:
            radicals.setdefault(e, []).append(f)
    return others + [
        _pow(to_expr(value(_mul([f.args[0] for f in fs]))), fs[0].args[1], known)
        for fs in radicals.values()
    ]


def _nonzero(e, known):
    v = value(e)
    return v != 0 if v is not None else holds(Ne(e, 0), known)


def _pow(base, exponent, known):
    vb, vx = value(base), value(exponent)
    if vb is not None and vx is not None:
        result = power(vb, vx)
        return Pow(base, exponent) if result is None else result
    if vb == 0:
        rest, c = _split_term(exponent)
        return Pow(base, rest) if value(c).re > 0 else Pow(base, exponent)
    if vb is not None and exponent.head == Add and _is_integer(exponent.args[0]):
        whole, rest = power(vb, value(exponent.args[0])), exponent.args[1:]
        if whole is not None and _coefficient(Mul, whole) is not None:
            return _collect(Mul, [whole, _pow(base, _sum(rest), known)], known)
    if vx is None:
        return Pow(base, exponent)
    if vx == 1:
        return base
    if vx == 0:
        return NumberKind(1) if holds(Ne(base, 0), known) else Pow(base, exponent)
    if vx.is_integer and base.head == exp:
        return exp(_collect(Mul, [exponent, base.args[0]], known))
    if vx.is_integer and base.head == Mul:
        return _collect(Mul, [_pow(f, exponent, known) for f in base.args], known)
    if vx.is_integer and base.head == Pow and (vx.re > 0 or _nonzero(base.args[0], known)):
        return _pow(base.args[0], _collect(Mul, [base.args[1], exponent], known), known)
    if vx.im == 0 and base.head == Mul:
        numbers = [f for f in base.args if value(f) is not None]
        rest = [f for f in base.args if value(f) is None]
        c = value(_mul(numbers)) if numbers else None
        if c is not None and c.im == 0 and c.re > 0:
            return _collect(Mul, [_pow(_mul(numbers), exponent, known),
                                  _pow(_mul(rest), exponent, known)], known)
    return Pow(base, exponent)

