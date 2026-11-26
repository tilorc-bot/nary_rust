"""
    >>> from nary import Add, Ne, NumberKind
    >>> from nary.identities import Equal, identities, inverse
    >>> from nary.rules import is_flat
    >>> identities(Add)[:3], is_flat(Add)
    ([associative, commutative, identity(0)], True)
    >>> identities(Add)[3:]
    [Equal(Add(a, a), Mul(2, a)), inverse(Mul(-1, a))]
    >>> inverse.statement
    Equal(f(a, i), e)
    >>> x = NumberKind("x")
    >>> Equal(x * 1, x).kind, Equal(x / x, 1, Ne(x, 0))
    (BoolKind, Equal(Mul(x, Pow(x, -1)), 1, Ne(x, 0)))
"""

from ._core import Expr, FunctionKind, declare_kind
from .domains import declare_function
from .kinds import BoolKind, NumberKind
from .logic import true
from .rules import flat, rule, unordered

__all__ = [
    "Equal", "absorbing", "associative", "commutative", "declare_identities",
    "identities", "identity", "inverse",
]


_equal_functions = {}
_names = {}


def Equal(lhs, rhs, when=None, name=None):
    """Both sides have no value, or the same value, where ``when`` holds; unlike Eq it has a value:

    >>> from nary import NumberKind, log
    >>> from nary.domains import domain
    >>> x = NumberKind("x")
    >>> e = Equal(log(x), 1)
    >>> e, domain(e.head)
    (Equal(log(x), 1), true)
    """
    if not isinstance(rhs, Expr):
        rhs = lhs.kind(rhs)
    key = (lhs.kind, when is not None)
    if key not in _equal_functions:
        kinds = (lhs.kind, lhs.kind) + ((BoolKind,) if when is not None else ())
        _equal_functions[key] = declare_function("Equal", *kinds, returns=BoolKind, domain=true)
    e = _equal_functions[key](lhs, rhs, *(() if when is None else (when,)))
    if name is not None and _names.setdefault(e, name) != name:
        raise ValueError(f"{e!r} is already named {_names[e]!r}")
    return e


def _is_equal(item):
    return isinstance(item, Expr) and item.head in _equal_functions.values()


class Law:
    """
    >>> identity(0), identity.statement
    (identity(0), Equal(f(s, e, t), f(s, t)))
    """

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
    """
    >>> from nary import NumberKind
    >>> from nary._core import declare_function
    >>> a = NumberKind("a")
    >>> G = declare_function("G", NumberKind, NumberKind, returns=NumberKind)
    >>> declare_identities(G, [identity(0), inverse(a), Equal(G(a, a), a, name="g_self")])
    [Rule(G(a, 0), a, name='g_identity'), Rule(G(a, a), 0, name='g_inverse'), Rule(G(a, a), a, name='g_self')]
    """
    if F in _blocks:
        raise ValueError(f"the identities of {F!r} are already declared")
    laws = [item for item in items if isinstance(item, Law)]
    units = [law.args[0] for law in laws if law.title == "identity"]
    x = NumberKind("a")
    rules, facts = [], []
    for item in items:
        if not (isinstance(item, Law) or _is_equal(item)):
            raise TypeError(f"{item!r} cannot be listed")
        if isinstance(item, Law) and item.params and item.name is None:
            name = f"{F.name.lower()}_{item.title}"
            item = Law(item.title, item.statement, item.params, item.args, item.when, name)
        if _is_equal(item):
            if item not in _names:
                raise ValueError(f"{item!r} in the block of {F!r} needs a name=")
            rules.append(rule(*item.args, name=_names[item]))
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
    names = [r.name for r in rules]
    if len(set(names)) < len(names):
        raise ValueError(f"two rules in the block of {F!r} have the same name")
    for fact in facts:
        fact(F)
    _blocks[F] = list(items)
    return rules


def identities(F):
    return list(_blocks.get(F, []))
