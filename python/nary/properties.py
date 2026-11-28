"""
    >>> from nary import Add, Mul, NumberKind, Pow
    >>> from nary.calculus import NumberFunction
    >>> from nary.functions import Lambda
    >>> Mul.is_associative, Mul.is_commutative, Mul.identity_element, Mul.absorbing_element
    (True, True, 1, 0)
    >>> Add.absorbing_element, Pow.is_associative, Pow.identity_element
    (None, False, None)
    >>> x = NumberKind("x")
    >>> f, square = NumberFunction("f"), Lambda(x, x * x)
    >>> f.is_commutative, f.identity_element, square.is_associative, square.absorbing_element
    (False, None, False, None)
    >>> x.is_commutative
    Traceback (most recent call last):
        ...
    AttributeError: 'Expr' object has no attribute 'is_commutative'
    >>> Mul.properties
    mappingproxy({'is_associative': True, 'is_commutative': True, 'identity_element': 1, 'absorbing_element': 0})
    >>> Pow.properties, f.properties
    (mappingproxy({}), mappingproxy({}))
"""

from types import MappingProxyType

from . import _core
from .rules import _check_declared_function, flat, rule, unordered

__all__ = ["declare_properties", "declare_property", "property_rules"]

_defaults = {}
_elements = set()
_declared = {}
_undeclared = {"properties": MappingProxyType({})}


def declare_property(name, element=False):
    """
    >>> declare_property("kind")
    Traceback (most recent call last):
        ...
    ValueError: kind is already an attribute of Expr
    >>> declare_property("properties")
    Traceback (most recent call last):
        ...
    ValueError: properties is already an attribute of functions
    >>> declare_property("is_even", element=True)
    Traceback (most recent call last):
        ...
    ValueError: is_even is True or False, so it cannot be an element
    """
    if name in _defaults:
        raise ValueError(f"{name} is already a property")
    if hasattr(_core.Expr, name):
        raise ValueError(f"{name} is already an attribute of Expr")
    if name == "properties":
        raise ValueError("properties is already an attribute of functions")
    if element and name.startswith("is_"):
        raise ValueError(f"{name} is True or False, so it cannot be an element")
    _defaults[name] = False if name.startswith("is_") else None
    for properties in (_undeclared, *_declared.values()):
        properties[name] = _defaults[name]
    if element:
        _elements.add(name)


declare_property("is_associative")
declare_property("is_commutative")
declare_property("identity_element", element=True)
declare_property("absorbing_element", element=True)


def _bind(F, name, value):
    if name not in _defaults:
        raise TypeError(f"{name} is not a property")
    if name.startswith("is_") and type(value) is not bool:
        raise TypeError(f"{name} must be True or False, got {value!r}")
    if name in _elements:
        return F(F.kind.output("a"), value).args[1]
    return value


def declare_properties(F, **given):
    """
    >>> from nary import NumberKind, declare_function
    >>> from nary.logic import true
    >>> G = declare_function("G", NumberKind, NumberKind, returns=NumberKind, domain=true)
    >>> declare_properties(G, is_commutative=1)
    Traceback (most recent call last):
        ...
    TypeError: is_commutative must be True or False, got 1
    >>> declare_properties(G, is_commutative=True, absorbing_element=true)
    Traceback (most recent call last):
        ...
    TypeError: G expects NumberKind, got BoolKind: true
    >>> declare_properties(G, is_commutative=True, identity_element=0)
    >>> G.is_commutative, G.identity_element, G.absorbing_element, property_rules(G)
    (True, 0, None, [Rule(G(a, 0), a, name='g_identity')])
    """
    _check_declared_function("declare_properties", F)
    if F in _declared:
        raise ValueError(f"the properties of {F!r} are already declared")
    bound = {name: _bind(F, name, value) for name, value in given.items()}
    if bound.get("is_associative"):
        flat(F)
    if bound.get("is_commutative"):
        unordered(F)
    has = {name: v for name, v in bound.items() if v is not None and v is not False}
    _declared[F] = {**_defaults, **bound, "properties": MappingProxyType(has)}


def _properties_of(F):
    return _declared.get(F, _undeclared)


_core._set_properties(_properties_of)


def property_rules(F):
    a, prefix = F.kind.output("a"), F.name.lower()
    unit, zero = F.identity_element, F.absorbing_element
    rules = []
    if unit is not None:
        rules.append(rule(F(a, unit), a, name=f"{prefix}_identity"))
    if zero is not None:
        rules.append(rule(F(a, zero), zero, name=f"{prefix}_absorbing"))
    return rules
