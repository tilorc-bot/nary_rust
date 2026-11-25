"""Identities: what holds for a function, declared in one block per function.

``declare_identities(F, items)`` lists, for the function ``F``, the laws
below and ``Equal`` statements, records the list (``identities(F)``) and
returns the rules it makes. The laws are stated once, with placeholders for
any function ``f``; these statements are not proved and nothing reads them.

    >>> from nary import Add
    >>> from nary.identities import identities, inverse
    >>> identities(Add)[:3]
    [associative, commutative, identity(0)]
    >>> inverse.statement
    Equal(f(a, i), e)
"""

from ._core import FunctionKind, declare_kind
from .kinds import NumberKind
from .rules import flat, rule, unordered

__all__ = [
    "Equal", "absorbing", "associative", "commutative", "declare_identities",
    "identities", "identity", "inverse",
]


class Equal:
    """``lhs`` and ``rhs`` both have no value or have the same value, where
    ``when`` holds."""

    def __init__(self, lhs, rhs, when=None, name=None):
        self.lhs, self.rhs, self.when, self.name = lhs, rhs, when, name

    def __repr__(self):
        extra = "" if self.when is None else f", when={self.when!r}"
        extra += "" if self.name is None else f", name={self.name!r}"
        return f"Equal({self.lhs!r}, {self.rhs!r}{extra})"


class Law:
    """A law that holds for any function it is listed for, given its
    parameters, as in ``identity(0)``, and where ``when`` holds."""

    def __init__(self, title, statement, params=(), args=None, when=None, name=None):
        self.title, self.statement, self.params = title, statement, params
        self.args, self.when, self.name = args, when, name

    def __call__(self, *args, when=None, name=None):
        if self.args is not None or len(args) != len(self.params):
            raise TypeError(f"{self.title} takes {len(self.params)} parameters")
        return Law(self.title, self.statement, self.params, args, when, name)

    def __repr__(self):
        if not self.params:
            return self.title
        return f"{self.title}({', '.join(map(repr, self.args or self.params))})"


PatternKind = declare_kind("PatternKind")
f = FunctionKind((), PatternKind, rest=PatternKind)("f")
a, b, e, i, z, s, t, u = (PatternKind(name) for name in "abeizstu")

associative = Law("associative", Equal(f(s, f(t), u), f(s, t, u)))
commutative = Law("commutative", Equal(f(s, a, t, b, u), f(s, b, t, a, u)))
identity = Law("identity", Equal(f(s, e, t), f(s, t)), (e,))
absorbing = Law("absorbing", Equal(f(s, z, t), z), (z,))
inverse = Law("inverse", Equal(f(a, i), e), (i,))

_blocks = {}


def declare_identities(F, items):
    """Record ``items`` as the identities of ``F`` and return its rules.

    ``associative`` and ``commutative`` record ``flat(F)`` and
    ``unordered(F)``. ``identity(e)``, ``absorbing(z)`` and ``inverse(i)``
    give the rules ``F(a, e) -> a``, ``F(a, z) -> z`` and ``F(a, i) -> e``
    (``a`` is ``NumberKind("a")``, ``e`` from the block's ``identity``), each
    with its ``when=`` and ``name=``, as is each ``Equal``.
    """
    if F in _blocks:
        raise ValueError(f"the identities of {F!r} are already declared")
    laws = [item for item in items if isinstance(item, Law)]
    units = [law.args[0] for law in laws if law.title == "identity"]
    x = NumberKind("a")
    rules, facts = [], []
    for item in items:
        if not isinstance(item, (Law, Equal)):
            raise TypeError(f"{item!r} cannot be listed")
        if item.name is None and (isinstance(item, Equal) or item.params):
            raise ValueError(f"{item!r} in the block of {F!r} needs a name=")
        if isinstance(item, Equal):
            rules.append(rule(item.lhs, item.rhs, when=item.when, name=item.name))
        elif item.title == "associative":
            facts.append(flat)
        elif item.title == "commutative":
            facts.append(unordered)
        elif item.title == "identity":
            rules.append(rule(F(x, item.args[0]), x, when=item.when, name=item.name))
        elif item.title == "absorbing":
            rules.append(rule(F(x, item.args[0]), item.args[0], when=item.when, name=item.name))
        elif item.title == "inverse":
            if not units:
                raise ValueError(f"inverse needs an identity in the block of {F!r}")
            rules.append(rule(F(x, item.args[0]), units[0], when=item.when, name=item.name))
    for fact in facts:
        fact(F)
    _blocks[F] = list(items)
    return rules


def identities(F):
    """The items listed for ``F``, or ``[]``."""
    return list(_blocks.get(F, []))
