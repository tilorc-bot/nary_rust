"""
    >>> from nary import BoolKind, NumberKind
    >>> from nary.domains import declare_function
    >>> from nary.generic import apply_generic, concretize, generic_of, placeholder
    >>> from nary.logic import true
    >>> K = placeholder("K")
    >>> Same = declare_function("Same", K("lhs"), K("rhs"), returns=BoolKind, domain=true)
    >>> Same, Same.kind
    (Same, FunctionKind((K, K), BoolKind))
    >>> SameNumber = concretize(Same, {K: NumberKind})
    >>> SameNumber.kind, SameNumber is concretize(Same, {K: NumberKind}), generic_of(SameNumber)
    (FunctionKind((NumberKind, NumberKind), BoolKind), True, Same)
    >>> apply_generic(Same, NumberKind("x"), 0).head is SameNumber
    True
    >>> apply_generic(Same, NumberKind("x"), BoolKind("p"))
    Traceback (most recent call last):
        ...
    TypeError: Same: K is NumberKind and BoolKind
"""

from functools import cache

from ._core import Expr, FunctionKind, Kind, Symbol, declare_kind
from .domains import declare_function, domain

__all__ = ["apply_generic", "concretize", "fill_from", "generic_of", "placeholder"]

_placeholders = set()
_concrete = {}
_generic = {}


@cache
def placeholder(name):
    kind = declare_kind(name)
    _placeholders.add(kind)
    return kind


def _parts(kind):
    if kind.inputs is not None:
        return (*kind.inputs, kind.output, *(() if kind.rest is None else (kind.rest,)))
    return tuple(p for p in kind.params if isinstance(p, Kind))


def _fill(kind, filling):
    if kind in filling:
        return filling[kind]
    if kind.inputs is not None:
        rest = None if kind.rest is None else _fill(kind.rest, filling)
        inputs = tuple(_fill(k, filling) for k in kind.inputs)
        return FunctionKind(inputs, _fill(kind.output, filling), rest=rest)
    if kind.family is not None:
        return kind.family(*(_fill(p, filling) if isinstance(p, Kind) else p for p in kind.params))
    return kind


def _match(parameter, kind, filling, name):
    if parameter in _placeholders:
        if filling.setdefault(parameter, kind) != kind:
            raise TypeError(f"{name}: {parameter!r} is {filling[parameter]!r} and {kind!r}")
    elif (parameter.inputs is None) == (kind.inputs is None) and parameter.family is kind.family:
        if len(_parts(parameter)) == len(_parts(kind)):
            for p, k in zip(_parts(parameter), _parts(kind)):
                _match(p, k, filling, name)


def fill_from(f, args):
    filling = {}
    positions = [p.kind if isinstance(p, Symbol) else p for p in f.params]
    positions += [f.kind.rest] * (len(args) - len(positions))
    for parameter, arg in zip(positions, args):
        if isinstance(arg, Expr) and parameter is not None:
            _match(parameter, arg.kind, filling, f.name)
    return filling


def _fill_parameter(parameter, name, filling):
    if isinstance(parameter, Symbol):
        return Symbol(_fill(parameter.kind, filling))
    kind = _fill(parameter, filling)
    return kind(name) if name else kind


def concretize(f, filling):
    if not filling:
        return f
    key = (f, frozenset(filling.items()))
    if key not in _concrete:
        names = f.names or (None,) * len(f.params)
        rest = f.kind.rest
        concrete = declare_function(
            f.name,
            *(_fill_parameter(p, n, filling) for p, n in zip(f.params, names)),
            rest=None if rest is None else _fill(rest, filling),
            returns=_fill(f.kind.output, filling),
            domain=domain(f),
        )
        _concrete[key] = concrete
        _generic[concrete] = f
    return _concrete[key]


def apply_generic(f, *args):
    return concretize(f, fill_from(f, args))(*args)


def generic_of(f):
    return _generic.get(f)
