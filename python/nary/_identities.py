"""
    >>> from nary import Add
    >>> from nary._identities import identities, inverse
    >>> identities(Add)[:3]
    [associative, commutative, identity(0)]
    >>> inverse.statement
    Equal(f(a, i), e)
"""

import copy

from ._core import FunctionKind, declare_kind
from .kinds import Many, NumberKind
from .rules import flat, rule, unordered

__all__ = [
    "Equal", "absorbing", "associative", "commutative", "composes", "declare_identities",
    "dominant", "heads", "idempotent", "identities", "identity", "inverse", "involution", "maps",
    "repeats", "undoes",
]


class Equal:
    """Both sides have no value, or the same value, where ``when`` holds:

    >>> from nary import Ne, NumberKind
    >>> x = NumberKind("x")
    >>> Equal(x / x, 1, when=Ne(x, 0), name="div_self")
    Equal(Mul(x, Pow(x, -1)), 1, when=Ne(x, 0), name='div_self')
    """

    def __init__(self, lhs, rhs, when=None, name=None):
        self.lhs, self.rhs, self.when, self.name = lhs, rhs, when, name

    def __repr__(self):
        extra = "" if self.when is None else f", when={self.when!r}"
        extra += "" if self.name is None else f", name={self.name!r}"
        return f"Equal({self.lhs!r}, {self.rhs!r}{extra})"


class Law:
    """
    >>> identity(0), identity.statement
    (identity(0), Equal(f(s, e, t), f(s, t)))
    """

    def __init__(self, title, statement, params=(), args=None, when=None, name=None, of=None,
                 normal=None):
        self.title, self.statement, self.params = title, statement, params
        self.args, self.when, self.name, self.of, self.normal = args, when, name, of or self, normal

    def __call__(self, *args, when=None, name=None, normal=None):
        if self.args is not None or len(args) != len(self.params):
            raise TypeError(f"{self.title} takes {len(self.params)} parameters")
        if normal not in (None, "merged", "split"):
            raise ValueError(f"normal must be 'merged', 'split' or None, got {normal!r}")
        return Law(self.title, self.statement, self.params, args, when, name, self, normal)

    def __repr__(self):
        if not self.params:
            return self.title
        return f"{self.title}({', '.join(map(repr, self.args or self.params))})"


PatternKind = declare_kind("PatternKind")
f = FunctionKind((Many(PatternKind),), PatternKind)("f")
g, plus = (FunctionKind((PatternKind, PatternKind), PatternKind)(name) for name in ("g", "plus"))
h, k = (FunctionKind((PatternKind,), PatternKind)(name) for name in "hk")
a, b, e, i, m, n, p, q, z, s, t, u = (PatternKind(name) for name in "abeimnpqzstu")

associative = Law("associative", Equal(f(s, f(t), u), f(s, t, u)))
commutative = Law("commutative", Equal(f(s, a, t, b, u), f(s, b, t, a, u)))
identity = Law("identity", Equal(f(s, e, t), f(s, t)), (e,))
absorbing = Law("absorbing", Equal(f(s, z, t), z), (z,))
dominant = Law("dominant", Equal(f(s, z, t), z), (z,))
inverse = Law("inverse", Equal(f(a, i), e), (i,))
idempotent = Law("idempotent", Equal(f(s, a, t, a, u), f(s, a, t, u)))
involution = Law("involution", Equal(h(h(a)), a))
repeats = Law("repeats", Equal(f(g(a, m), g(a, n)), g(a, plus(m, n))), (g(a, n), n))
maps = Law("maps", Equal(h(f(a, s)), plus(h(a), h(f(s)))), (h(a), a, p, q))
undoes = Law("undoes", Equal(h(k(a)), a), (k(a),))
composes = Law("composes", Equal(g(g(a, m), n), g(a, plus(m, n))), (g(a, n), n, plus))

_blocks = {}


def declare_identities(F, items):
    """
    >>> from nary import NumberKind
    >>> from nary._core import declare_function
    >>> a = NumberKind("a")
    >>> G = declare_function("G", NumberKind, NumberKind, returns=NumberKind)
    >>> declare_identities(G, [identity(0), inverse(a), idempotent])
    [Rule(G(a, 0), a, name='g_identity'), Rule(G(a, a), 0, name='g_inverse'), Rule(G(a, a), a, name='g_idempotent')]
    """
    if F in _blocks:
        raise ValueError(f"the identities of {F!r} are already declared")
    for item in items:
        if not isinstance(item, Law) or item.args is None and item.params:
            raise TypeError(f"{item!r} cannot be listed: a block lists only laws")
    items = [copy.copy(item) for item in items]
    for item in items:
        item.name = item.name or f"{F.name.lower()}_{item.title}"
    names = [item.name for item in items]
    if len(set(names)) < len(names):
        raise ValueError(f"two laws in the block of {F!r} have the same name")
    units = [item.args[0] for item in items if item.of is identity]
    x = F.kind.output("a")
    rules, facts = [], []
    for item in items:
        if item.title == "associative":
            facts.append(flat)
        elif item.title == "commutative":
            facts.append(unordered)
        elif item.title == "identity":
            rules.append(rule(F(x, item.args[0]), x, when=item.when, name=item.name))
        elif item.title in ("absorbing", "dominant"):
            rules.append(rule(F(x, item.args[0]), item.args[0], when=item.when, name=item.name))
        elif item.title == "inverse":
            if not units:
                raise ValueError(f"inverse needs an identity in the block of {F!r}")
            rules.append(rule(F(x, item.args[0]), units[0], when=item.when, name=item.name))
        elif item.title == "idempotent":
            rules.append(rule(F(x, x), x, when=item.when, name=item.name))
        elif item.title == "involution":
            rules.append(rule(F(F(x)), x, when=item.when, name=item.name))
        elif item.title == "repeats":
            form, count = item.args
            twice = form.head(*(count.kind(2) if arg == count else x for arg in form.args))
            rules.append(rule(F(x, x), twice, when=item.when, name=item.name))
    for fact in facts:
        fact(F)
    _blocks[F] = list(items)
    return rules


def identities(F):
    return list(_blocks.get(F, []))


def heads():
    return list(_blocks)
