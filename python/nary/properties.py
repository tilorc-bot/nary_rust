"""
    >>> import nary.arithmetic_rules
    >>> from nary import Add, Mul, Pow
    >>> properties(Mul)
    Properties(associative=True, commutative=True, identity=1, absorbing=0)
    >>> properties(Mul).identity, properties(Add).absorbing, properties(Pow).associative
    (1, None, False)
    >>> property_rules(Mul)
    [Rule(Mul(a, 1), a, name='mul_identity'), Rule(Mul(a, 0), 0, name='mul_absorbing')]
"""

from types import SimpleNamespace

from .rules import flat, rule, unordered

__all__ = ["declare_properties", "declare_property", "properties", "property_rules"]

_defaults = {}
_elements = set()
_declared = {}


class Properties(SimpleNamespace):
    def __getattr__(self, name):
        if name not in _defaults:
            raise AttributeError(f"{name} is not a property")
        return _defaults[name]

    def __setattr__(self, name, value):
        raise AttributeError("Properties cannot be changed")


def declare_property(name, default=None, element=False):
    """
    >>> declare_property("identity")
    Traceback (most recent call last):
        ...
    ValueError: identity is already a property
    """
    if name in _defaults:
        raise ValueError(f"{name} is already a property")
    _defaults[name] = default
    if element:
        _elements.add(name)


declare_property("associative", default=False)
declare_property("commutative", default=False)
declare_property("identity", element=True)
declare_property("absorbing", element=True)


def _element(F, value):
    return F(F.kind.output("a"), value).args[1]


def declare_properties(F, **given):
    """
    >>> from nary import NumberKind, declare_function
    >>> from nary.logic import true
    >>> G = declare_function("G", NumberKind, NumberKind, returns=NumberKind, domain=true)
    >>> declare_properties(G, idenity=0)
    Traceback (most recent call last):
        ...
    TypeError: idenity is not a property
    >>> declare_properties(G, commutative=True, absorbing=true)
    Traceback (most recent call last):
        ...
    TypeError: G expects NumberKind, got BoolKind: true
    >>> declare_properties(G, commutative=True, identity=0)
    >>> properties(G), property_rules(G)
    (Properties(commutative=True, identity=0), [Rule(G(a, 0), a, name='g_identity')])
    """
    if F in _declared:
        raise ValueError(f"the properties of {F!r} are already declared")
    for name in given:
        if name not in _defaults:
            raise TypeError(f"{name} is not a property")
    bound = {
        name: _element(F, value) if name in _elements else value
        for name, value in given.items()
    }
    if bound.get("associative"):
        flat(F)
    if bound.get("commutative"):
        unordered(F)
    _declared[F] = Properties(**bound)


def properties(F):
    return _declared.get(F, Properties())


def property_rules(F):
    a, prefix = F.kind.output("a"), F.name.lower()
    unit, zero = properties(F).identity, properties(F).absorbing
    rules = []
    if unit is not None:
        rules.append(rule(F(a, unit), a, name=f"{prefix}_identity"))
    if zero is not None:
        rules.append(rule(F(a, zero), zero, name=f"{prefix}_absorbing"))
    return rules
