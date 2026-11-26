"""autosimp simplifies the arguments first, then applies the step of the head.

    >>> from nary import E, Ne, NumberKind, exp, log, pi, sin
    >>> from nary.autosimp import autosimp
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> autosimp(2 * x + y - x + 3 - 1)
    Add(2, x, y)
    >>> autosimp(sin(-x) * x * x), autosimp(exp(x) * exp(-x)), autosimp(sin(pi / 6))
    (Mul(-1, Pow(x, 2), sin(x)), 1, Pow(2, -1))

A step that is sound only under a condition waits for the condition.

    >>> autosimp(x / x), autosimp(x / x, known=[Ne(x, 0)])
    (Pow(x, 0), 1)
    >>> autosimp(log(y) - log(y)), autosimp(log(y) - log(y), known=[Ne(y, 0)])
    (Mul(0, log(y)), 0)
"""

from fractions import Fraction
from math import gcd, prod

from . import arithmetic_rules
from ._core import Expr
from .arithmetic import Add, Mul, Pow
from .constants import E, I, pi
from .elementary import cos, exp, log, sin, tan
from .functions import Lambda, is_lambda
from .kinds import BoolKind, NumberKind
from .logic import And, Not, Or, false, true
from .properties import (
    has_value, holds, integer, negative, nonzero, number, number_factors, positive, rational,
    real,
)
from .relational import Eq, Ge, Gt, Le, Lt, Ne, re
from .rules import rule

__all__ = ["RULES", "STEPS", "autosimp", "key", "node"]

ZERO, ONE, MINUS_ONE = NumberKind(0), NumberKind(1), NumberKind(-1)
HALF, HALF_FRACTION = Pow(2, -1), Fraction(1, 2)
a, b, p = NumberKind("a"), NumberKind("b"), BoolKind("p")

RULES = {
    Pow: [
        *arithmetic_rules.power,
        rule(Pow(1, a), 1, name="one_pow"),
        rule(Pow(0, a), 0, when=Gt(re(a), 0), name="zero_pow"),
        rule(Pow(E, a), exp(a), name="e_pow"),
    ],
    exp: [
        rule(exp(0), 1, name="exp_zero"),
        rule(exp(1), E, name="exp_one"),
        *arithmetic_rules.exponential,
    ],
    log: [
        rule(log(1), 0, name="log_one"),
        rule(log(E), 1, name="log_e"),
        rule(log(exp(a)), a, when=Eq(re(a), a), name="log_exp"),
    ],
    re: [
        rule(re(a), a, when=Eq(re(a), a), name="re_real"),
        rule(re(I), 0, name="re_i"),
    ],
    Not: [
        rule(Not(true), false, name="not_true"),
        rule(Not(false), true, name="not_false"),
        rule(Not(Not(p)), p, name="not_not"),
        rule(Not(Eq(a, b)), Ne(a, b), name="not_eq"),
        rule(Not(Ne(a, b)), Eq(a, b), name="not_ne"),
        rule(Not(Lt(a, b)), Ge(a, b), name="not_lt"),
        rule(Not(Le(a, b)), Gt(a, b), name="not_le"),
        rule(Not(Gt(a, b)), Le(a, b), name="not_gt"),
        rule(Not(Ge(a, b)), Lt(a, b), name="not_ge"),
    ],
}


def autosimp(e, known=()):
    if not isinstance(e, Expr):
        raise TypeError(f"autosimp expects an expression, got {e!r}")
    return _simp(e, frozenset(known))


def _simp(e, known):
    if e.head is None:
        return e
    if is_lambda(e):
        *variables, body = e.args
        return Lambda(tuple(variables), _simp(body, known))
    return node(_simp(e.head, known), [_simp(arg, known) for arg in e.args], known)


def node(head, args, known=frozenset()):
    """
    >>> from nary import NumberKind, sin
    >>> x = NumberKind("x")
    >>> node(Mul, [x, Pow(x, 2)]), node(sin, [Mul(-1, x)])
    (Pow(x, 3), Mul(-1, sin(x)))
    """
    e = head(*args)
    for r in RULES.get(head, ()):
        bindings = _match(r.pattern, e, {})
        if bindings is not None and _allowed(r, bindings, known):
            return _build(r.replacement, bindings, known)
    return STEPS[head](list(e.args), known) if head in STEPS else e


def _match(pattern, e, bindings):
    if pattern.is_symbol:
        if pattern.kind != e.kind or bindings.get(pattern, e) != e:
            return None
        return {**bindings, pattern: e}
    if pattern.head is None or e.head is None:
        return bindings if pattern == e else None
    if pattern.head != e.head or len(pattern.args) != len(e.args):
        return None
    for sub, arg in zip(pattern.args, e.args):
        bindings = _match(sub, arg, bindings)
        if bindings is None:
            return None
    return bindings


def _allowed(r, bindings, known):
    if r.condition is not None and not holds(_substitute(r.condition, bindings), known):
        return False
    return all(has_value(bindings[v], known) for v in r.erased)


def _substitute(e, bindings):
    if e.head is None:
        return bindings.get(e, e)
    return e.head(*(_substitute(arg, bindings) for arg in e.args))


def _build(e, bindings, known):
    if e.head is None:
        return bindings.get(e, e)
    return node(e.head, [_build(arg, bindings, known) for arg in e.args], known)


def key(e):
    """
    >>> from nary import NumberKind, pi, sin
    >>> x = NumberKind("x")
    >>> sorted([sin(x), pi, x, HALF, 3], key=key)
    [Pow(2, -1), 3, x, pi, sin(x)]
    """
    if not isinstance(e, Expr):
        e = NumberKind(e)
    if rational(e) is not None:
        return (0, rational(e))
    if e.head is None:
        return (1 if e.is_symbol else 2, e.name, repr(e.kind))
    return (3, key(e.head), len(e.args), tuple(key(arg) for arg in e.args))


def _flatten(head, args):
    return [x for arg in args for x in (arg.args if arg.head == head else (arg,))]


def _assemble(head, numbers, others, unit):
    items = [*numbers, *sorted(others, key=key)]
    if not items:
        return unit
    return items[0] if len(items) == 1 else head(*items)


def _coeff(e):
    if e.head != Mul:
        return Fraction(1), e
    c, rest = Fraction(1), []
    for f in e.args:
        if rational(f) is None:
            rest.append(f)
        else:
            c *= rational(f)
    return c, rest[0] if len(rest) == 1 else Mul(*rest)


def _add(args, known):
    total, terms = Fraction(0), {}
    for t in _flatten(Add, args):
        if rational(t) is not None:
            total += rational(t)
        else:
            c, rest = _coeff(t)
            terms[rest] = terms.get(rest, 0) + c
    collected = [node(Mul, [number(c), t], known) for t, c in terms.items()]
    numbers = [number(total)] if total else []
    return _assemble(Add, numbers, [t for t in collected if t != ZERO], ZERO)


def _base_exp(f):
    if f.head == Pow:
        return f.args
    if f.head == exp:
        return E, f.args[0]
    return f, ONE


def _term(x):
    return ONE if rational(x) is not None else _coeff(x)[1]


def _radical(f):
    if f == I:
        return -1, HALF_FRACTION
    if f.head == Pow and integer(f.args[0]) and (rational(f.args[1]) or 0) % 1 > 0:
        return integer(f.args[0]), rational(f.args[1])
    return None


def _same_exponent(factors, known):
    by_exponent, rest = {}, []
    for f in factors:
        if f.head == Pow and (rational(f.args[0]) or 0) > 0:
            by_exponent.setdefault(f.args[1], []).append(rational(f.args[0]))
        else:
            rest.append(f)
    return rest + [node(Pow, [number(prod(bs)), x], known) for x, bs in by_exponent.items()]


def _mul(args, known):
    c, groups, radicals = Fraction(1), {}, []
    for f in _flatten(Mul, args):
        if rational(f) is not None:
            c *= rational(f)
        elif _radical(f) is not None:
            radicals.append(_radical(f))
        else:
            base, x = _base_exp(f)
            groups.setdefault((base, _term(x)), []).append((x, f))
    factors = [f for group in groups.values() for _, f in group]
    if c == 0:
        return _assemble(Mul, [ZERO], {f for f in factors if not has_value(f, known)}, ZERO)
    out = [f for (base, _), group in groups.items() for f in _powers(base, group, known)]
    c, numeric = _radicals(c, radicals)
    out = _same_exponent(out, known) + numeric
    if any(rational(f) is not None or f.head == Mul for f in out):
        return _mul([*number_factors(c), *out], known)
    if c != 1 and len(out) == 1 and out[0].head == Add:
        return node(Add, [node(Mul, [number(c), t], known) for t in out[0].args], known)
    return _assemble(Mul, number_factors(c) if c != 1 else [], out, ONE)


def _nonpositive(x):
    return rational(x) is not None and rational(x) <= 0


def _powers(base, group, known):
    """
    >>> from nary import NumberKind
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> node(Mul, [x ** 2, x ** -3]), node(Mul, [x ** 2, x ** -1, x ** y])
    (Pow(x, -1), Mul(Pow(x, -1), Pow(x, 2), Pow(x, y)))
    """
    exponents = [x for x, _ in group]
    if nonzero(base, known) or all(positive(x, known) for x in exponents):
        return [_merged(base, group, known)]
    pos = [(x, f) for x, f in group if positive(x, known)]
    nonpos = [(x, f) for x, f in group if _nonpositive(x)]
    rest = [f for x, f in group if not positive(x, known) and not _nonpositive(x)]
    decided = pos + nonpos
    if decided and _nonpositive(node(Add, [x for x, _ in decided], known)):
        parts = [decided]
    else:
        parts = [pos, nonpos]
    return [_merged(base, part, known) for part in parts if part] + rest


def _merged(base, group, known):
    if len(group) == 1:
        return group[0][1]
    return node(Pow, [base, node(Add, [x for x, _ in group], known)], known)


def _root(n, k):
    x = 1 << -(-n.bit_length() // k)
    while True:
        y = ((k - 1) * x + n // x ** (k - 1)) // k
        if y >= x:
            return x
        x = y


def _factors(n):
    for k in range(n.bit_length(), 1, -1):
        if _root(n, k) ** k == n:
            return {_root(n, k): k}
    found, d = {}, 2
    while d < 2 ** 15 and d * d <= n:
        while n % d == 0:
            found[d], n = found.get(d, 0) + 1, n // d
        d += 1
    return {**found, n: 1} if n > 1 else found


def _minus_one(s):
    if (2 * s).denominator == 1:
        return [[ONE, I, MINUS_ONE, Mul(-1, I)][int(2 * s) % 4]]
    whole, part = divmod(s, 1)
    return [MINUS_ONE] * (whole % 2) + [Pow(-1, number(part))]


def _integer_power(n, s):
    if s == HALF_FRACTION and n < 0:
        return [I, *_power(Fraction(-n), s)]
    sign = _minus_one(s) if n < 0 else []
    if s < 0:
        return sign + _power(Fraction(1, abs(n)), -s)
    m, q = abs(n), s.denominator
    if _root(m, q) ** q == m:
        return [number(_root(m, q) ** s.numerator), *sign]
    out, radicals, rest = 1, [], {}
    for prime, k in _factors(m).items():
        whole, part = divmod(k * s.numerator, q)
        out *= prime ** whole
        if part and gcd(part, q) != 1:
            radicals.append(Pow(prime, number(Fraction(part, q))))
        elif part:
            rest[prime] = part
    g = gcd(*rest.values())
    base = prod(prime ** (k // g) for prime, k in rest.items())
    if base == m and out == 1 and not radicals:
        return None
    return [number(out), *radicals, *(_power(Fraction(base), Fraction(g, q)) if rest else []), *sign]


def _rational_power(r, s):
    if s < 0:
        return _minus_one(s) + _power(-1 / r, -s) if r < 0 else _power(1 / r, -s)
    k = s.numerator // s.denominator + 1
    rest = Fraction(k * s.denominator - s.numerator, s.denominator)
    numerator = [] if r.numerator == 1 else _power(Fraction(r.numerator), s)
    return numerator + _power(Fraction(r.denominator), rest) + [number(Fraction(1, r.denominator ** k))]


def _power(r, s):
    if s.denominator == 1:
        return [number(r ** int(s))]
    if r in (0, 1):
        return [number(r)]
    if r == -1:
        return _minus_one(s)
    if r.denominator != 1:
        return _rational_power(r, s)
    return _integer_power(r.numerator, s) or [Pow(number(r), number(s))]


def _numeric_power(r, s):
    """
    >>> _numeric_power(Fraction(12), Fraction(1, 2)), _numeric_power(Fraction(-2), Fraction(1, 2))
    ([2, Pow(3, Pow(2, -1))], [I, Pow(2, Pow(2, -1))])
    """
    if r == 0 and s <= 0:
        return None
    if r.denominator == 1 and s.denominator != 1 and r not in (-1, 0, 1):
        return _integer_power(r.numerator, s)
    return _power(r, s)


def _radicals(c, powers):
    """
    >>> from nary import NumberKind
    >>> node(Mul, [Pow(2, HALF), Pow(6, HALF)]), node(Mul, [Pow(-8, Pow(3, -1)), Pow(2, Pow(3, -1))])
    (Mul(2, Pow(3, Pow(2, -1))), Mul(2, Pow(-2, Pow(3, -1))))
    """
    minus, exponents, combined = Fraction(0), {}, {}
    for b, e in powers:
        minus, b = (minus + e, -b) if b < 0 else (minus, b)
        if b != 1:
            exponents.setdefault(b, []).append(e)
    for b, es in exponents.items():
        combined.setdefault(sum(es), []).append(b)
    pending = []
    for e, bases in combined.items():
        whole, e = divmod(e, 1)
        c *= Fraction(prod(bases)) ** whole
        pending += [(prod(bases), e)] if e else []
    new, i = {}, 0
    while i < len(pending):
        bi, ei = pending[i]
        for j in range(i + 1, len(pending)):
            bj, ej = pending[j]
            g = gcd(bi, bj) if bi != 1 else 1
            if g != 1:
                whole, e = divmod(ei + ej, 1)
                c *= Fraction(g) ** whole
                pending += [(g, e)] if e else []
                pending[j], bi = (bj // g, ej), bi // g
        for f in _power(Fraction(bi), ei) if bi != 1 else []:
            if rational(f) is not None:
                c *= rational(f)
            else:
                new.setdefault(rational(f.args[1]), []).append(integer(f.args[0]))
        i += 1
    whole, part = divmod(minus, 1)
    c, out = (-c if whole % 2 else c), []
    if part == HALF_FRACTION:
        out.append(I)
    elif part in new:
        new[part] = [-prod(new[part])]
    elif part:
        out.append(Pow(-1, number(part)))
    return c, out + [Pow(prod(bases), number(e)) for e, bases in new.items()]


def _nonnegative(x, known):
    return positive(x, known) or (rational(x) is not None and rational(x) >= 0)


def _pow(args, known):
    base, x = args
    if rational(base) is not None and rational(x) is not None:
        factors = _numeric_power(rational(base), rational(x))
        return Pow(base, x) if factors is None else node(Mul, factors, known)
    n = integer(x)
    if base == I and rational(x) is not None:
        whole, part = divmod(rational(x), 2)
        rest = [I] if part == 1 else [Pow(I, number(part))] if part else []
        return node(Mul, [*_minus_one(whole), *rest], known)
    if base.head == Pow and _nested(*base.args, x, known):
        return node(Pow, [base.args[0], node(Mul, [base.args[1], x], known)], known)
    if base.head == exp and (n is not None or real(base.args[0], known)):
        return node(exp, [node(Mul, [x, base.args[0]], known)], known)
    if base.head == Mul and n:
        return node(Mul, [node(Pow, [f, x], known) for f in base.args], known)
    if base.head == Mul and rational(x) is not None and _coeff(base)[1] == I:
        value = _imaginary_power(_coeff(base)[0], rational(x), known)
        if value is not None:
            return value
    if base.head == Mul and rational(x) is not None:
        return _split_power(base, x, known)
    if _gaussian(base) and rational(x) is not None:
        value = _gaussian_power(*_gaussian(base), rational(x), known)
        if value is not None:
            return value
    if base == ZERO and _coeff(x)[0] > 0 and _coeff(x)[0] != 1:
        return node(Pow, [ZERO, _coeff(x)[1]], known)
    return Pow(base, x)


def _gaussian(e):
    if e.head != Add or len(e.args) != 2 or rational(e.args[0]) is None:
        return None
    c, rest = _coeff(e.args[1])
    return (rational(e.args[0]), c) if rest == I else None


def _complex(z, known):
    return node(Add, [number(z[0]), node(Mul, [number(z[1]), I], known)], known)


def _times(z, n):
    out = (Fraction(1), Fraction(0))
    for _ in range(n):
        out = (out[0] * z[0] - out[1] * z[1], out[0] * z[1] + out[1] * z[0])
    return out


def _square_root(r):
    p, q = _root(r.numerator, 2), _root(r.denominator, 2)
    return Fraction(p, q) if p * p == r.numerator and q * q == r.denominator else None


def _complex_power(scale, z, p, known):
    if p > 0:
        return node(Mul, [scale, _complex(_times(z, p), known)], known)
    w = _times(z, -p)
    conjugate = _times((z[0], -z[1]), -p)
    return node(Mul, [scale, number(1 / (w[0] ** 2 + w[1] ** 2)), _complex(conjugate, known)], known)


def _gaussian_power(r, i, s, known):
    """
    >>> node(Pow, [3 + 4 * I, HALF]), node(Pow, [3 + I, -1])
    (Add(2, I), Add(Mul(3, Pow(10, -1)), Mul(-1, Pow(10, -1), I)))
    """
    if s == -1:
        return _complex_power(ONE, (r, i), -1, known)
    d = _square_root(r * r + i * i)
    if s.denominator != 2 or d is None:
        return None
    scale = node(Pow, [number((d - r) / 2), number(s)], known)
    return _complex_power(scale, ((d + r) / abs(i), Fraction(1 if i > 0 else -1)), s.numerator, known)


def _imaginary_power(c, s, known):
    """
    >>> node(Pow, [2 * I, HALF]), node(Pow, [-8 * I, HALF])
    (Add(1, I), Add(2, Mul(-2, I)))
    """
    r = _square_root(abs(c) / 2)
    if s.denominator != 2 or r is None:
        return None
    unit = _complex((1, 1 if c > 0 else -1), known)
    return node(Mul, [node(Pow, [number(r), number(s.numerator)], known),
                      node(Pow, [unit, number(s.numerator)], known)], known)


def _nested(inner, y, x, known):
    """
    >>> from nary import NumberKind
    >>> x, y = NumberKind("x"), NumberKind("y")
    >>> node(Pow, [x ** HALF, y]), node(Pow, [x ** -1, -1]), node(Pow, [x ** y, 2])
    (Pow(x, Mul(Pow(2, -1), y)), Pow(Pow(x, -1), -1), Pow(x, Mul(2, y)))
    """
    if rational(Pow(inner, y)) is not None:
        return False
    if positive(inner, known) and real(y, known):
        return True
    if integer(x) is None and not (rational(y) is not None and abs(rational(y)) < 1):
        return False
    return nonzero(inner, known) or _nonnegative(y, known) or _nonnegative(x, known)


def _split_power(base, x, known):
    """
    >>> from nary import NumberKind
    >>> y = NumberKind("y")
    >>> node(Pow, [Mul(-2, E, y), HALF])
    Mul(Pow(2, Pow(2, -1)), Pow(Mul(-1, y), Pow(2, -1)), exp(Pow(2, -1)))
    """
    c, rest = _coeff(base)
    factors = rest.args if rest.head == Mul else (rest,)
    pulled = [f for f in factors if positive(f, known)]
    others = [f for f in factors if not positive(f, known)]
    if c < 0 and others:
        others, c = [MINUS_ONE, *others], -c
    elif c < 0:
        others, c = [number(c)], 1
    if c != 1:
        pulled.append(number(c))
    if not pulled:
        return Pow(base, x)
    if others:
        pulled.append(node(Mul, others, known))
    return node(Mul, [node(Pow, [f, x], known) for f in pulled], known)


def _pi_multiple(e, unit=pi):
    if rational(e) == 0:
        return Fraction(0)
    c, rest = _coeff(e)
    return c if rest == unit else None


_SUMS = {
    12: (3, 4), 20: (4, 5), 30: (5, 6), 15: (6, 10), 24: (6, 8), 40: (8, 10), 60: (20, 30), 120: (40, 60),
}


def _at(f, r, known):
    return node(f, [_times_pi(r, known)], known)


def _times_pi(r, known):
    return node(Mul, [number(r), pi], known)


def _evaluated(*values):
    return all(v.head not in (sin, cos, tan) for v in values)


def _inverse(e, known):
    return node(Pow, [e, MINUS_ONE], known)


def _negative(e, known):
    return node(Mul, [MINUS_ONE, e], known)


ROOT5 = Pow(5, HALF)
_COS_VALUES = {
    Fraction(1, 3): HALF,
    Fraction(1, 5): Add(Mul(Pow(4, -1), ROOT5), Pow(4, -1)),
    Fraction(2, 5): Add(Mul(Pow(4, -1), ROOT5), Mul(-1, Pow(4, -1))),
}
_TAN_VALUES = {
    1: Pow(Add(1, Mul(-2, Pow(5, -1), ROOT5)), HALF),
    2: Pow(Add(5, Mul(-2, ROOT5)), HALF),
    3: Pow(Add(1, Mul(2, Pow(5, -1), ROOT5)), HALF),
    4: Pow(Add(5, Mul(2, ROOT5)), HALF),
}


def _sin_at(r, arg, known):
    if r.denominator == 1:
        return ZERO
    if r > 1:
        return _negative(_at(sin, r - 1, known), known)
    if 2 * r > 1:
        return _at(sin, 1 - r, known)
    value = _at(cos, (r + Fraction(3, 2)) % 2, known)
    if value.head != cos:
        return value
    return None if _times_pi(r, known) == arg else _at(sin, r, known)


def _cos_at(r, arg, known):
    """
    >>> autosimp(cos(pi / 12))
    Add(Mul(Pow(4, -1), Pow(2, Pow(2, -1))), Mul(Pow(4, -1), Pow(6, Pow(2, -1))))
    >>> autosimp(sin(Mul(104, Pow(105, -1), pi)))
    sin(Mul(Pow(105, -1), pi))
    """
    p, q = r.numerator, r.denominator
    if q <= 2:
        return [ONE, ZERO, MINUS_ONE, ZERO][int(2 * r)]
    if p > q or 2 * p > q:
        return _negative(_at(cos, r - 1 if p > q else 1 - r, known), known)
    if q in _SUMS:
        a, b = (Fraction(p, d) for d in _SUMS[q])
        values = [_at(cos, t, known) for t in (a, b, HALF_FRACTION - a, HALF_FRACTION - b)]
        if not _evaluated(*values):
            return None
        return node(Add, [node(Mul, values[:2], known), node(Mul, values[2:], known)], known)
    if r in _COS_VALUES:
        return _simp(_COS_VALUES[r], known)
    if q % 2 or q > 12 or not _evaluated(_at(cos, 2 * r, known)):
        return None
    return node(Pow, [node(Mul, [HALF, node(Add, [ONE, _at(cos, 2 * r, known)], known)], known), HALF], known)


def _tan_at(r, arg, known):
    p, q = r.numerator % r.denominator, r.denominator
    if q == 1:
        return ZERO
    if q in (5, 10):
        n = 10 * p // q
        return _simp(_TAN_VALUES[n] if n < 5 else Mul(-1, _TAN_VALUES[10 - n]), known)
    c, s = _at(cos, 2 * r, known), _at(cos, 2 * r - HALF_FRACTION, known)
    if q % 2 == 0 and _evaluated(c, s) and s != ZERO:
        quotient = node(Mul, [c, _inverse(s, known)], known)
        return node(Add, [_inverse(s, known), _negative(quotient, known)], known)
    if q % 2 == 0 and _evaluated(c, s):
        return None
    if q in _SUMS:
        a, b = (_at(tan, Fraction(p, d), known) for d in _SUMS[q])
        if not _evaluated(a, b):
            return None
        top = node(Add, [a, _negative(b, known)], known)
        return node(Mul, [top, _inverse(node(Add, [ONE, node(Mul, [a, b], known)], known), known)], known)
    t = (r + HALF_FRACTION) % 1 - HALF_FRACTION
    c, s = _at(cos, t, known), _at(cos, t - HALF_FRACTION, known)
    if _evaluated(c, s):
        return None if c == ZERO else node(Mul, [s, _inverse(c, known)], known)
    return None if _times_pi(t, known) == arg else _at(tan, t, known)


_AT = {sin: _sin_at, cos: _cos_at, tan: _tan_at}


def _minus(e):
    if e.head == Add:
        signs = [_minus(t) for t in e.args]
        return signs.count(True) > signs.count(False)
    return (rational(e) if rational(e) is not None else _coeff(e)[0]) < 0


def _peel(arg):
    for t in arg.args if arg.head == Add else ():
        k = _pi_multiple(t)
        if k is not None and k - k % HALF_FRACTION:
            m = k - k % HALF_FRACTION
            return m, [u for u in arg.args if u != t] + [Mul(*number_factors(k - m), pi)]
    return None, None


def _shifted(f, m, x, known):
    """
    >>> from nary import NumberKind
    >>> x = NumberKind("x")
    >>> autosimp(sin(x + pi / 2)), autosimp(cos(x + pi)), autosimp(tan(x - 3 * pi))
    (cos(x), Mul(-1, cos(x)), tan(x))
    """
    s, c = [(0, 1), (1, 0), (0, -1), (-1, 0)][int(2 * m) % 4]
    if f == tan:
        return node(tan, [x], known) if s == 0 else None
    same, other = (c, s) if f == sin else (c, -s)
    g = f if s == 0 else (cos if f == sin else sin)
    return node(Mul, [NumberKind(same if s == 0 else other), node(g, [x], known)], known)


def _trigonometric(f, odd):
    def step(args, known):
        (arg,) = args
        r = _pi_multiple(arg)
        value = None if r is None else _AT[f](r % 2, arg, known)
        if value is not None:
            return value
        m, rest = _peel(arg)
        shifted = None if m is None else _shifted(f, m, node(Add, rest, known), known)
        if shifted is not None:
            return shifted
        if not _minus(arg):
            return f(arg)
        flipped = node(f, [node(Mul, [MINUS_ONE, arg], known)], known)
        return node(Mul, [MINUS_ONE, flipped], known) if odd else flipped
    return step


def _constant(e):
    return not e.is_symbol and (e.head is None or all(_constant(a) for a in e.args))


def _exp(args, known):
    """
    >>> from nary import NumberKind
    >>> x = NumberKind("x")
    >>> autosimp(exp(Mul(9, Pow(4, -1), I, pi))), autosimp(exp(pi * log(x)), known=[Ne(x, 0)])
    (exp(Mul(Pow(4, -1), I, pi)), Pow(x, pi))
    """
    (arg,) = args
    r = _pi_multiple(arg, Mul(I, pi))
    if r is not None and r.denominator <= 2:
        return [ONE, I, MINUS_ONE, Mul(-1, I)][int(2 * r) % 4]
    if r is not None and r != (r + 1) % 2 - 1:
        return node(exp, [node(Mul, [number((r + 1) % 2 - 1), I, pi], known)], known)
    factors = list(arg.args) if arg.head == Mul else [arg]
    logs = [f for f in factors if f.head == log]
    others = [f for f in factors if f.head != log]
    if len(logs) == 1 and all(_constant(f) and real(f, known) for f in others):
        if nonzero(logs[0].args[0], known):
            return node(Pow, [logs[0].args[0], node(Mul, others, known)], known)
    if arg.head == Add:
        out, kept = [], []
        for t in arg.args:
            v = exp(t) if t == ONE else node(exp, [t], known)
            out, kept = (out, kept + [v.args[0]]) if v.head == exp else (out + [v], kept)
        if out or kept != list(arg.args):
            return node(Mul, [*out, node(exp, [node(Add, kept, known)], known)], known)
    return exp(arg)


def _log(args, known):
    """
    >>> autosimp(log(Mul(-2, Pow(3, HALF))))
    Add(Mul(I, pi), log(Mul(2, Pow(3, Pow(2, -1)))))
    >>> autosimp(log(Pow(-12, HALF)))
    Add(Mul(Pow(2, -1), I, pi), log(Mul(2, Pow(3, Pow(2, -1)))))
    """
    (arg,) = args
    r = rational(arg)
    if r is not None and r.numerator == 1 and r.denominator > 1:
        return _negative(node(log, [number(r.denominator)], known), known)
    if _constant(arg) and negative(arg, known):
        return node(Add, [node(log, [_negative(arg, known)], known), Mul(I, pi)], known)
    factors = list(arg.args) if arg.head == Mul else [arg]
    others = [f for f in factors if f != I]
    if len(others) == len(factors) - 1 and all(rational(f) is not None or _radical(f) for f in others):
        c = node(Mul, others, known)
        if positive(c, known) or negative(c, known):
            sign = 1 if positive(c, known) else -1
            half = node(Mul, [number(sign * HALF_FRACTION), I, pi], known)
            return node(Add, [node(log, [node(Mul, [NumberKind(sign), c], known)], known), half], known)
    return log(arg)


def _re(args, known):
    (arg,) = args
    if arg.head == Add:
        return node(Add, [node(re, [t], known) for t in arg.args], known)
    if arg.head == Mul:
        reals = [f for f in arg.args if real(f, known)]
        others = [f for f in arg.args if not real(f, known)]
        if reals and others:
            rest = others[0] if len(others) == 1 else Mul(*others)
            return node(Mul, [*reals, node(re, [rest], known)], known)
    return re(arg)


def _difference(args, known):
    lhs, rhs = args
    return node(Add, [lhs, node(Mul, [MINUS_ONE, rhs], known)], known)


def _equality(head, when_zero):
    def step(args, known):
        d = _difference(args, known)
        if rational(d) == 0:
            return true if when_zero else false
        if nonzero(d, known):
            return false if when_zero else true
        return head(*args)
    return step


def _order(head, test):
    def step(args, known):
        d = _difference(args, known)
        if not all(real(arg, known) for arg in args):
            return head(*args)
        if rational(d) is not None:
            return true if test(rational(d)) else false
        if positive(d, known) or negative(d, known):
            return true if test(1 if positive(d, known) else -1) else false
        return head(*args)
    return step


RELATIONS = (Eq, Ne, Lt, Gt, Le, Ge)


def _lattice(head, unit, zero):
    def step(args, known):
        items = set(_flatten(head, args)) - {unit}
        if zero in items or any(
            x.head in RELATIONS and node(Not, [x], known) in items and has_value(x, known)
            for x in items
        ):
            return zero
        return _assemble(head, [], items, unit)
    return step


STEPS = {
    Add: _add,
    Mul: _mul,
    Pow: _pow,
    sin: _trigonometric(sin, odd=True),
    cos: _trigonometric(cos, odd=False),
    tan: _trigonometric(tan, odd=True),
    exp: _exp,
    log: _log,
    re: _re,
    Eq: _equality(Eq, when_zero=True),
    Ne: _equality(Ne, when_zero=False),
    Lt: _order(Lt, lambda d: d < 0),
    Gt: _order(Gt, lambda d: d > 0),
    Le: _order(Le, lambda d: d <= 0),
    Ge: _order(Ge, lambda d: d >= 0),
    And: _lattice(And, true, false),
    Or: _lattice(Or, false, true),
}
