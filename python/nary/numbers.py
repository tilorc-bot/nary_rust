"""
    >>> from nary import Add, Mul, Pow, I, Lt
    >>> value(Add(1, Mul(2, I), Pow(I, 2)))
    Number(0, 2)
    >>> to_expr(Number(Fraction(1, 2), -3))
    Add(Pow(2, -1), Mul(-3, I))
    >>> power(Number(25), Number(Fraction(1, 3)))
    Pow(5, Mul(2, Pow(3, -1)))
    >>> power(Number(5), Number(Fraction(1, 2))) is None
    True
    >>> compare(Lt, Number(1), Number(2)), compare(Lt, Number(0, 1), Number(2))
    (true, None)
"""

from dataclasses import dataclass
from fractions import Fraction
from math import gcd, isqrt, prod

from .arithmetic import Add, Mul, Pow
from .constants import I
from .kinds import NumberKind
from .logic import false, true
from .relational import Eq, Ge, Gt, Le, Lt, Ne

__all__ = ["Number", "compare", "is_canonical_number", "power", "real_part", "to_expr", "value"]


@dataclass(frozen=True, eq=False)
class Number:
    """
    >>> Number(1, 2) * Number(1, -2) + 1, Number(0, 1) ** -3, Number(2) == 2
    (Number(6, 0), Number(0, 1), True)
    """

    re: Fraction
    im: Fraction = Fraction(0)

    def __post_init__(self):
        object.__setattr__(self, "re", Fraction(self.re))
        object.__setattr__(self, "im", Fraction(self.im))

    def __repr__(self):
        return f"Number({self.re}, {self.im})"

    def __eq__(self, other):
        other = _number(other)
        return other is not None and (self.re, self.im) == (other.re, other.im)

    def __hash__(self):
        return hash(self.re) if self.im == 0 else hash((self.re, self.im))

    def __add__(self, other):
        other = _number(other)
        return Number(self.re + other.re, self.im + other.im)

    def __neg__(self):
        return Number(-self.re, -self.im)

    def __sub__(self, other):
        return self + -_number(other)

    def __mul__(self, other):
        o = _number(other)
        return Number(self.re * o.re - self.im * o.im, self.re * o.im + self.im * o.re)

    __radd__, __rmul__ = __add__, __mul__

    def __rsub__(self, other):
        return -self + other

    def __pow__(self, n):
        if n < 0:
            norm = self.re**2 + self.im**2
            return Number(self.re / norm, -self.im / norm) ** -n
        result, base = Number(1), self
        while n:
            if n & 1:
                result *= base
            base, n = base * base, n >> 1
        return result

    @property
    def is_integer(self):
        return self.im == 0 and self.re.denominator == 1


def _number(x):
    return x if isinstance(x, Number) else Number(x) if isinstance(x, (int, Fraction)) else None


def value(e):
    """
    >>> from nary import Pow, NumberKind
    >>> value(Pow(2, -1)), value(Pow(0, -1)), value(Pow(2, Pow(2, -1))), value(NumberKind("x"))
    (Number(1/2, 0), None, None, None)
    """
    if e.is_literal:
        return Number(e.value)
    if e == I:
        return Number(0, 1)
    if e.head not in (Add, Mul, Pow):
        return None
    vs = [value(a) for a in e.args]
    if None in vs:
        return None
    if e.head == Add:
        return sum(vs, Number(0))
    if e.head == Mul:
        return prod(vs, start=Number(1))
    b, x = vs
    if not x.is_integer or (b == 0 and x.re <= 0):
        return None
    return b ** int(x.re)


def _rational_factors(r):
    if r.denominator == 1:
        return [NumberKind(r.numerator)]
    q = Pow(r.denominator, -1)
    return [q] if r.numerator == 1 else [NumberKind(r.numerator), q]


def _mul(factors):
    return factors[0] if len(factors) == 1 else Mul(*factors)


def to_expr(v):
    """
    >>> to_expr(Number(Fraction(-2, 3))), to_expr(Number(0, Fraction(1, 2))), to_expr(Number(1, 1))
    (Mul(-2, Pow(3, -1)), Mul(Pow(2, -1), I), Add(1, I))
    """
    v = _number(v)
    re = _mul(_rational_factors(v.re))
    if v.im == 0:
        return re
    im = I if v.im == 1 else Mul(*_rational_factors(v.im), I)
    return im if v.re == 0 else Add(re, im)


def is_canonical_number(e):
    """
    >>> from nary import Mul
    >>> is_canonical_number(Mul(2, I)), is_canonical_number(Mul(I, 2))
    (True, False)
    """
    v = value(e)
    return v is not None and to_expr(v) == e


def _nthroot(n, k):
    lo, hi = 0, 1 << (n.bit_length() // k + 1)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        lo, hi = (mid, hi) if mid**k <= n else (lo, mid - 1)
    return lo


def _factor(n):
    primes, p = {}, 2
    while p < 2**15 and p * p <= n:
        while n % p == 0:
            primes[p], n = primes.get(p, 0) + 1, n // p
        p += 1
    if n > 1:
        k = next(k for k in range(n.bit_length(), 0, -1) if _nthroot(n, k) ** k == n)
        primes[_nthroot(n, k)] = k
    return primes


def _integer_power(n, x):
    coefficient, radicals, grouped = Fraction(1), [], {}
    for prime, e in _factor(n).items():
        whole, rest = divmod(e * x.numerator, x.denominator)
        coefficient *= Fraction(prime) ** whole
        if rest and gcd(rest, x.denominator) != 1:
            radicals.append((prime, Fraction(rest, x.denominator)))
        elif rest:
            grouped[prime] = rest
    if grouped:
        g = gcd(*grouped.values())
        radicals.append((prod(p ** (r // g) for p, r in grouped.items()), Fraction(g, x.denominator)))
    return coefficient, radicals


def _positive_power(b, x):
    coefficient, radicals = Fraction(1), {}
    for n, y in ((b.numerator, x), (b.denominator, -x)):
        c, rs = _integer_power(n, y)
        coefficient *= c
        for base, e in rs:
            radicals[e] = radicals.get(e, 1) * base
    return coefficient, sorted((base, e) for e, base in radicals.items())


def _product(coefficient, factors):
    c = to_expr(coefficient)
    head = [] if coefficient == 1 and factors else c.args if c.head == Mul else [c]
    return _mul([*head, *factors]) if head or factors else c


def _radical(base, e):
    return Pow(base, to_expr(Number(e)))


def _sqrt(r):
    root = Fraction(isqrt(r.numerator), isqrt(r.denominator))
    return root if root * root == r else None


def _gaussian_sqrt(z):
    d = _sqrt(z.re**2 + z.im**2)
    r, s = (None, None) if d is None else (_sqrt((d + z.re) / 2), _sqrt((d - z.re) / 2))
    return None if r is None or s is None else Number(r, s if z.im > 0 else -s)


def power(b, x):
    """
    >>> F = Fraction
    >>> power(Number(F(2, 3)), Number(F(3, 2)))
    Mul(2, Pow(9, -1), Pow(6, Pow(2, -1)))
    >>> power(Number(-4), Number(F(1, 2))), power(Number(3, 4), Number(F(1, 2)))
    (Mul(2, I), Add(2, I))
    >>> power(Number(-8), Number(F(1, 3)))
    Mul(2, Pow(-1, Pow(3, -1)))
    """
    if b == 0:
        return NumberKind(0) if x.re > 0 else None
    if x.is_integer:
        return to_expr(b ** int(x.re))
    if x.im != 0:
        return None
    y = x.re
    if b.im != 0:
        root = _gaussian_sqrt(b) if y.denominator == 2 else None
        return None if root is None else to_expr(root ** y.numerator)
    c, radicals = _positive_power(abs(b.re), y)
    coefficient, factors = Number(c), [_radical(base, e) for base, e in radicals]
    if b.re < 0:
        if y.denominator != 2 and c == 1 and radicals == [(-b.re, y)]:
            return None
        whole, rest = divmod(y.numerator, y.denominator)
        coefficient *= Number(-1) ** whole
        if y.denominator == 2:
            coefficient *= Number(0, 1)
        else:
            factors.insert(0, _radical(-1, Fraction(rest, y.denominator)))
    result = _product(coefficient, factors)
    return None if result == Pow(to_expr(b), to_expr(x)) else result


def compare(op, a, b):
    """
    >>> from nary import Eq, Ge
    >>> compare(Eq, Number(1, 1), Number(1, 1)), compare(Ge, Number(1), Number(2))
    (true, false)
    """
    if op in (Eq, Ne):
        return true if (a == b) == (op == Eq) else false
    if a.im != 0 or b.im != 0:
        return None
    holds = {Lt: a.re < b.re, Le: a.re <= b.re, Gt: a.re > b.re, Ge: a.re >= b.re}[op]
    return true if holds else false


def real_part(v):
    """
    >>> real_part(Number(Fraction(1, 2), 3))
    Number(1/2, 0)
    """
    return Number(v.re)
