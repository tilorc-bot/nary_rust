"""
    >>> from nary import Add
    >>> from nary._identities import identities, inverse
    >>> identities(Add)[:3]
    [associative, commutative, identity(0)]
    >>> inverse.statement
    Equal(f(a, i), e)
"""

from ._core import Expr, FunctionKind, declare_kind
from .kinds import Many
from .rules import flat, rule, unordered

__all__ = [
    "Equal", "absorbing", "associative", "commutative", "declare_identities",
    "idempotent", "identities", "identity", "inverse",
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

    def __init__(self, title, statement, params=(), args=None, when=None, name=None, of=None):
        self.title, self.statement, self.params = title, statement, params
        self.args, self.when, self.name, self.of = args, when, name, of or self

    def __call__(self, *args, when=None, name=None):
        if self.args is not None or len(args) != len(self.params):
            raise TypeError(f"{self.title} takes {len(self.params)} parameters")
        return Law(self.title, self.statement, self.params, args, when, name, self)

    def __repr__(self):
        if not self.params:
            return self.title
        return f"{self.title}({', '.join(map(repr, self.args or self.params))})"


PatternKind = declare_kind("PatternKind")
f = FunctionKind((Many(PatternKind),), PatternKind)("f")
a, b, e, i, z, s, t, u = (PatternKind(name) for name in "abeizstu")

associative = Law("associative", Equal(f(s, f(t), u), f(s, t, u)))
commutative = Law("commutative", Equal(f(s, a, t, b, u), f(s, b, t, a, u)))
identity = Law("identity", Equal(f(s, e, t), f(s, t)), (e,))
absorbing = Law("absorbing", Equal(f(s, z, t), z), (z,))
inverse = Law("inverse", Equal(f(a, i), e), (i,))
idempotent = Law("idempotent", Equal(f(s, a, t, a, u), f(s, a, t, u)))

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
    for item in items:
        if not isinstance(item, (Law, Equal)):
            raise TypeError(f"{item!r} cannot be listed")
        if isinstance(item, Law) and item.args is None and item.params:
            raise TypeError(f"{item!r} cannot be listed: give it its parameters")
    items = [_bind(F, item) for item in items]
    laws = [item for item in items if isinstance(item, Law)]
    titles = {law.title for law in laws}
    if "idempotent" in titles and not {"associative", "commutative"} <= titles:
        raise ValueError(f"idempotent needs associative and commutative in the block of {F!r}")
    units = [law.args[0] for law in laws if law.title == "identity"]
    x = F.kind.output("a")
    rules, facts = [], []
    for item in items:
        if isinstance(item, Law) and item.name is None:
            name = f"{F.name.lower()}_{item.title}"
            item = Law(item.title, item.statement, item.params, item.args, item.when, name, item.of)
        if isinstance(item, Equal) and item.name is None:
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
        elif item.title == "idempotent":
            rules.append(rule(F(x, x), x, when=item.when, name=item.name))
    names = [r.name for r in rules]
    if len(set(names)) < len(names):
        raise ValueError(f"two rules in the block of {F!r} have the same name")
    for fact in facts:
        fact(F)
    _blocks[F] = list(items)
    return rules


def _bind(F, item):
    """
    >>> from nary import Mul
    >>> _bind(Mul, absorbing(0)).args[0].is_literal
    True
    """
    if not isinstance(item, Law) or not item.params:
        return item
    x = F.kind.output("a")
    args = [F(x, arg).args[1] if _is_element(param) else arg
            for param, arg in zip(item.params, item.args)]
    return Law(item.title, item.statement, item.params, args, item.when, item.name, item.of)


def _is_element(param):
    """
    >>> _is_element(e), _is_element(f), _is_element("n")
    (True, False, False)
    """
    return isinstance(param, Expr) and param.is_symbol and param.kind == PatternKind


def identities(F):
    return list(_blocks.get(F, []))
