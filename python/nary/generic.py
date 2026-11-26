"""
    >>> from nary import BoolKind, NumberKind
    >>> from nary.generic import Generic, kind_variable
    >>> from nary.logic import true
    >>> K = kind_variable("K")
    >>> Same = Generic("Same", K("lhs"), K("rhs"), returns=BoolKind, domain=true)
    >>> x, p = NumberKind("x"), BoolKind("p")
    >>> Same(x, 0), Same(p, p).head.kind, Same(p, p).lhs
    (Same(x, 0), FunctionKind((BoolKind, BoolKind), BoolKind), p)
    >>> Same(x, 0).head in Same, Same(x, x).head is Same(x, 0).head, x.head in Same
    (True, True, False)
    >>> Same(x, p)
    Traceback (most recent call last):
        ...
    TypeError: Same: K is NumberKind and BoolKind
"""

from ._core import Expr, FunctionKind, Kind, Symbol, declare_kind
from .domains import declare_function

__all__ = ["Generic", "kind_variable"]

_variables = set()


def kind_variable(name):
    kind = declare_kind(name)
    _variables.add(kind)
    return kind


def _kind_of(parameter):
    return parameter if isinstance(parameter, Kind) else parameter.kind


def _match(parameter, kind, binding, name):
    if parameter in _variables:
        bound = binding.setdefault(parameter, kind)
        if bound != kind:
            raise TypeError(f"{name}: {parameter!r} is {bound!r} and {kind!r}")
    elif parameter.inputs is not None and kind.inputs is not None:
        for p, k in zip((*parameter.inputs, parameter.output), (*kind.inputs, kind.output)):
            _match(p, k, binding, name)


def _fill(kind, binding):
    if kind in _variables:
        return binding[kind]
    if kind.inputs is None:
        return kind
    return FunctionKind(tuple(_fill(k, binding) for k in kind.inputs), _fill(kind.output, binding))


def _variables_in(kind, found):
    if kind in _variables:
        if kind not in found:
            found.append(kind)
    elif kind.inputs is not None:
        for k in (*kind.inputs, kind.output):
            _variables_in(k, found)
    return found


def _fill_parameter(parameter, binding):
    if isinstance(parameter, Symbol):
        return Symbol(_fill(parameter.kind, binding))
    if isinstance(parameter, Expr):
        return _fill(parameter.kind, binding)(parameter.name)
    return _fill(parameter, binding)


class Generic:
    """
    >>> from nary import BoolKind, NumberKind
    >>> from nary.logic import true
    >>> K, L = kind_variable("K"), kind_variable("L")
    >>> Pick = Generic("Pick", K, L, returns=K, domain=true)
    >>> Pick.variables, Pick[NumberKind, BoolKind].kind
    ([K, L], FunctionKind((NumberKind, BoolKind), NumberKind))
    >>> Pick(NumberKind("x"), BoolKind("p")).head is Pick[NumberKind, BoolKind]
    True
    """

    def __init__(self, name, *parameters, returns, domain):
        self.name, self.parameters, self.returns, self.domain = name, parameters, returns, domain
        self.variables = []
        for kind in (*map(_kind_of, parameters), returns):
            _variables_in(kind, self.variables)
        self.specific = {}

    def __getitem__(self, kinds):
        kinds = kinds if isinstance(kinds, tuple) else (kinds,)
        if len(kinds) != len(self.variables):
            raise TypeError(f"{self.name} has {len(self.variables)} kind variables, got {len(kinds)}")
        if kinds not in self.specific:
            binding = dict(zip(self.variables, kinds))
            self.specific[kinds] = declare_function(
                self.name,
                *(_fill_parameter(p, binding) for p in self.parameters),
                returns=_fill(self.returns, binding),
                domain=self.domain,
            )
        return self.specific[kinds]

    def __call__(self, *args):
        binding = {}
        for parameter, arg in zip(self.parameters, args):
            if isinstance(arg, Expr):
                _match(_kind_of(parameter), arg.kind, binding, self.name)
        unknown = [v for v in self.variables if v not in binding]
        if unknown:
            raise TypeError(f"{self.name}: the arguments do not give {unknown}")
        return self[tuple(binding[v] for v in self.variables)](*args)

    def __contains__(self, function):
        return any(function is f for f in self.specific.values())

    def __repr__(self):
        return f"Generic({self.name!r})"
