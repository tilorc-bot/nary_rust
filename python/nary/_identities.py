"""
    >>> from nary import Add
    >>> from nary._identities import identities, inverse
    >>> identities(Add)[:3]
    [associative, commutative, identity(0)]
    >>> inverse.statement
    Equal(f(a, i), e)

A law is an expression whose parameters have the kind its head returns.

    >>> unit = identities(Add)[2]
    >>> unit.kind, unit.args[0].kind, law_of(unit)
    (LawKind, NumberKind, identity(e))
"""

from typing import NamedTuple

from ._core import FunctionKind, declare_constant, declare_function, declare_kind
from .kinds import Many
from .rules import flat, rule, unordered

__all__ = [
    "Equal", "LawKind", "absorbing", "associative", "commutative", "declare_identities",
    "identities", "identity", "inverse", "law_of",
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


LawKind = declare_kind("LawKind")
_laws = {}


class Listed(NamedTuple):
    law: "Law"
    args: tuple
    when: object
    name: object


class Law:
    """
    >>> from nary import NumberKind
    >>> identity, identity.statement
    (identity(e), Equal(f(s, e, t), f(s, t)))
    >>> identity(0)
    Listed(law=identity(e), args=(0,), when=None, name=None)
    >>> identity.bind(NumberKind, (0,)), associative.bind(NumberKind, ())
    (identity(0), associative)
    """

    def __init__(self, title, statement, params=(), fact=None, sides=None, needs=None):
        self.title, self.statement, self.params = title, statement, params
        self.fact, self.sides, self.needs = fact, sides, needs
        self._heads = {}
        if not params:
            self._constant = declare_constant(title, LawKind)
            _laws[self._constant] = self

    def __call__(self, *args, when=None, name=None):
        if len(args) != len(self.params):
            raise TypeError(f"{self.title} takes {len(self.params)} parameters")
        return Listed(self, args, when, name)

    def bind(self, kind, args):
        if not self.params:
            return self._constant
        if kind not in self._heads:
            head = declare_function(self.title, *(kind for _ in self.params), returns=LawKind)
            self._heads[kind] = head
            _laws[head] = self
        return self._heads[kind](*args)

    def __repr__(self):
        if not self.params:
            return self.title
        return f"{self.title}({', '.join(map(repr, self.params))})"


def law_of(e):
    """
    >>> from nary import Add
    >>> [law_of(e) for e in identities(Add) if not isinstance(e, Equal)]
    [associative, commutative, identity(e), inverse(i)]
    """
    return _laws[e if e.is_atom else e.head]


PatternKind = declare_kind("PatternKind")
f = FunctionKind((Many(PatternKind),), PatternKind)("f")
a, b, e, i, z, s, t, u = (PatternKind(name) for name in "abeizstu")

associative = Law("associative", Equal(f(s, f(t), u), f(s, t, u)), fact=flat)
commutative = Law("commutative", Equal(f(s, a, t, b, u), f(s, b, t, a, u)), fact=unordered)
identity = Law("identity", Equal(f(s, e, t), f(s, t)), (e,), sides=lambda F, x, e: (F(x, e), x))
absorbing = Law("absorbing", Equal(f(s, z, t), z), (z,), sides=lambda F, x, z: (F(x, z), z))
inverse = Law(
    "inverse", Equal(f(a, i), e), (i,), sides=lambda F, x, i, e: (F(x, i), e), needs=identity,
)

_blocks = {}


def _listed(item):
    if isinstance(item, Law) and not item.params:
        return item()
    if not isinstance(item, (Listed, Equal)):
        raise TypeError(f"{item!r} cannot be listed")
    return item


def declare_identities(F, items):
    """
    >>> from nary import NumberKind
    >>> from nary._core import declare_function
    >>> a = NumberKind("a")
    >>> G = declare_function("G", NumberKind, NumberKind, returns=NumberKind)
    >>> declare_identities(G, [identity(0), inverse(a), Equal(G(a, a), a, name="g_self")])
    [Rule(G(a, 0), a, name='g_identity'), Rule(G(a, a), 0, name='g_inverse'), Rule(G(a, a), a, name='g_self')]
    >>> identities(G)
    [identity(0), inverse(a), Equal(G(a, a), a, name='g_self')]
    """
    if F in _blocks:
        raise ValueError(f"the identities of {F!r} are already declared")
    listed = [_listed(item) for item in items]
    kind = F.kind.output
    entries = [
        item if isinstance(item, Equal) else item.law.bind(kind, item.args) for item in listed
    ]
    block = {law_of(entry): entry for entry in entries if not isinstance(entry, Equal)}
    x = kind("a")
    rules, facts = [], []
    for item, entry in zip(listed, entries):
        if isinstance(item, Equal):
            if item.name is None:
                raise ValueError(f"{item!r} in the block of {F!r} needs a name=")
            rules.append(rule(item.lhs, item.rhs, when=item.when, name=item.name))
            continue
        law = item.law
        if law.fact is not None:
            facts.append(law.fact)
        if law.sides is None:
            continue
        if law.needs is not None and law.needs not in block:
            raise ValueError(f"{law.title} needs an {law.needs.title} in the block of {F!r}")
        needed = block[law.needs].args if law.needs is not None else ()
        name = f"{F.name.lower()}_{law.title}" if item.name is None else item.name
        lhs, rhs = law.sides(F, x, *entry.args, *needed)
        rules.append(rule(lhs, rhs, when=item.when, name=name))
    names = [r.name for r in rules]
    if len(set(names)) < len(names):
        raise ValueError(f"two rules in the block of {F!r} have the same name")
    for fact in facts:
        fact(F)
    _blocks[F] = entries
    return rules


def identities(F):
    return list(_blocks.get(F, []))
