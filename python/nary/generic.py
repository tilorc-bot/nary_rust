"""
    >>> from nary import BoolKind, NumberKind, declare_kind
    >>> from nary.domains import declare_function
    >>> from nary.generic import concretize, generic_of
    >>> from nary.logic import true
    >>> K = declare_kind("K")
    >>> Same = declare_function("Same", K("lhs"), K("rhs"), returns=BoolKind, domain=true)
    >>> Same, Same.kind
    (Same, FunctionKind((K, K), BoolKind))
    >>> SameNumber = concretize(Same, {K: NumberKind})
    >>> SameNumber.kind, SameNumber(NumberKind("x"), 0).lhs
    (FunctionKind((NumberKind, NumberKind), BoolKind), x)
    >>> SameNumber is concretize(Same, {K: NumberKind}), generic_of(SameNumber) is Same
    (True, True)
"""

from ._core import FunctionKind, Symbol
from .domains import declare_function, domain

__all__ = ["concretize", "generic_of"]

_concrete = {}
_generic = {}


def _fill(kind, filling):
    if kind in filling:
        return filling[kind]
    if kind.inputs is None:
        return kind
    rest = None if kind.rest is None else _fill(kind.rest, filling)
    return FunctionKind(
        tuple(_fill(k, filling) for k in kind.inputs), _fill(kind.output, filling), rest=rest
    )


def _fill_parameter(parameter, name, filling):
    if isinstance(parameter, Symbol):
        return Symbol(_fill(parameter.kind, filling))
    kind = _fill(parameter, filling)
    return kind(name) if name else kind


def concretize(f, filling):
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


def generic_of(f):
    return _generic.get(f)
