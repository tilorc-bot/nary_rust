"""rule checks a rule and returns it.

    >>> from nary import BoolKind, Ne, NumberKind
    >>> from nary.logic import Not
    >>> from nary.rules import rule
    >>> a, p = NumberKind("a"), BoolKind("p")
    >>> r = rule(a / a, 1, when=Ne(a, 0))
    >>> r
    Rule(Mul(a, Pow(a, -1)), 1, when=Ne(a, 0))

A Rule keeps its pattern, replacement, condition and name.

    >>> r.pattern, r.replacement, r.condition, r.name
    (Mul(a, Pow(a, -1)), 1, Ne(a, 0), None)

The variable a is erased because it is not in the replacement.

    >>> r.variables, r.erased
    ((a,), (a,))

A rule can have a name.

    >>> rule(Not(Not(p)), p, name="double negation")
    Rule(Not(Not(p)), p, name='double negation')

Every symbol of the replacement must be in the pattern.

    >>> rule(a + 0, a + NumberKind("b"))
    Traceback (most recent call last):
        ...
    ValueError: every symbol of a rule must appear in its pattern, but b is in the replacement only

The symbols inside computed(...) are literal variables, which are never erased.

    >>> from nary.rules import computed
    >>> m, n = NumberKind("m"), NumberKind("n")
    >>> r = rule(m * a + n * a, computed(m + n) * a, name="collect")
    >>> r.replacement, r.literal_variables, r.erased
    (Mul(computed(Add(m, n)), a), (m, n), ())
"""

from ._core import Expr, Kind
from .domains import declare_function
from .functions import is_lambda
from .kinds import BoolKind, NumberKind
from .logic import true

__all__ = [
    "Rule", "computation", "computed", "computes", "flat", "is_flat",
    "is_unordered", "rule", "unordered",
]

_unordered = set()
_flat = set()
_computations = {}

computed = declare_function("computed", NumberKind, returns=NumberKind, domain=true)


def _subexpressions(e):
    stack = [e]
    while stack:
        e = stack.pop()
        yield e
        if e.head is not None:
            stack.extend(reversed((e.head, *e.args)))


def _symbols(e):
    symbols = []
    for sub in _subexpressions(e):
        if is_lambda(sub):
            raise ValueError(
                f"a rule cannot contain a Lambda yet, got {sub!r}: variables "
                f"bound by a lambda need a design that does not exist yet"
            )
        if sub.is_symbol and sub not in symbols:
            symbols.append(sub)
    return symbols


def _literal_variables(e):
    if e.is_symbol:
        return [e]
    if e.is_literal:
        return []
    if e.head in _computations:
        return [symbol for arg in e.args for symbol in _literal_variables(arg)]
    raise ValueError(
        f"inside computed(...) only symbols, literals and functions recorded "
        f"with computes() are allowed, got {e!r}"
    )


class Rule:
    __slots__ = (
        "condition", "erased", "literal_variables", "name", "pattern", "replacement",
        "variables",
    )

    def __init__(self, pattern, replacement, when=None, name=None):
        if not isinstance(pattern, Expr):
            raise TypeError(f"the pattern of a rule must be an expression, got {pattern!r}")
        if pattern.is_symbol:
            raise ValueError(
                f"the pattern of a rule cannot be a bare symbol, got {pattern!r}: "
                f"it would match every expression of its kind"
            )
        if not isinstance(replacement, Expr):
            literals = getattr(pattern.kind, "literals", None) or ()
            if type(replacement) not in literals:
                raise TypeError(
                    f"the replacement must be an expression or a literal of {pattern.kind!r}, "
                    f"got {type(replacement).__name__}: {replacement!r}"
                )
            replacement = pattern.kind(replacement)
        if replacement.kind is not pattern.kind:
            raise TypeError(
                f"the replacement must be of the pattern's kind {pattern.kind!r}, "
                f"got {replacement.kind!r}: {replacement!r}"
            )
        if when is not None and not (isinstance(when, Expr) and when.kind is BoolKind):
            raise TypeError(f"the condition of a rule must be a BoolKind expression, got {when!r}")
        if name is not None and not isinstance(name, str):
            raise TypeError(f"the name of a rule must be a str or None, got {name!r}")

        for where, e in (("pattern", pattern), ("condition", when)):
            if e is not None and any(sub == computed for sub in _subexpressions(e)):
                raise ValueError(
                    f"computed(...) may appear only in the replacement of a rule, "
                    f"but the {where} is {e!r}"
                )
        literal_variables = []
        for sub in _subexpressions(replacement):
            if sub.head == computed:
                for symbol in _literal_variables(sub.args[0]):
                    if symbol not in literal_variables:
                        literal_variables.append(symbol)

        variables = _symbols(pattern)
        in_replacement = _symbols(replacement)
        in_condition = _symbols(when) if when is not None else []
        kinds = {}
        for symbol in variables + in_replacement + in_condition:
            kind = kinds.setdefault(symbol.name, symbol.kind)
            if kind is not symbol.kind:
                raise ValueError(
                    f"a rule cannot have two symbols named {symbol.name} of different "
                    f"kinds, got {kind!r} and {symbol.kind!r}"
                )
        for where, symbols in (("replacement", in_replacement), ("condition", in_condition)):
            for symbol in symbols:
                if symbol not in variables:
                    raise ValueError(
                        f"every symbol of a rule must appear in its pattern, "
                        f"but {symbol!r} is in the {where} only"
                    )

        set_ = object.__setattr__
        set_(self, "pattern", pattern)
        set_(self, "replacement", replacement)
        set_(self, "condition", when)
        set_(self, "name", name)
        set_(self, "variables", tuple(variables))
        set_(self, "erased", tuple(v for v in variables if v not in in_replacement))
        set_(self, "literal_variables", tuple(literal_variables))

    def __setattr__(self, attribute, value):
        raise AttributeError("a Rule cannot be changed")

    def __repr__(self):
        parts = [repr(self.pattern), repr(self.replacement)]
        if self.condition is not None:
            parts.append(f"when={self.condition!r}")
        if self.name is not None:
            parts.append(f"name={self.name!r}")
        return f"Rule({', '.join(parts)})"


def rule(pattern, replacement, when=None, name=None):
    return Rule(pattern, replacement, when=when, name=name)


def _is_declared_function(e):
    return isinstance(e, Expr) and e.is_constant and e.kind.inputs is not None


def _check_declared_function(caller, f):
    if not _is_declared_function(f):
        raise TypeError(f"{caller} expects a declared function, got {f!r}")


def unordered(f):
    _check_declared_function("unordered", f)
    positions = f.params + ((f.kind.rest,) if f.kind.rest is not None else ())
    if not positions or not all(isinstance(p, Kind) for p in positions):
        raise ValueError(
            f"unordered needs a function whose arguments can be reordered, got {f!r} "
            f"declared with {f.params!r}, rest={f.kind.rest!r}"
        )
    if len(set(positions)) != 1:
        raise ValueError(
            f"unordered needs a function whose arguments all have one kind, got {f!r} "
            f"of kind {f.kind!r}"
        )
    if f in _unordered:
        raise ValueError(f"{f!r} is already recorded as unordered")
    _unordered.add(f)


def flat(f):
    _check_declared_function("flat", f)
    if f.kind.inputs or f.kind.rest is not f.kind.output:
        raise ValueError(
            f"flat needs a function taking any number of arguments of the kind it "
            f"returns, and no others, got {f!r} of kind {f.kind!r}"
        )
    if f in _flat:
        raise ValueError(f"{f!r} is already recorded as flat")
    _flat.add(f)


def is_unordered(f):
    _check_declared_function("is_unordered", f)
    return f in _unordered


def is_flat(f):
    _check_declared_function("is_flat", f)
    return f in _flat


def computes(f, integers):
    _check_declared_function("computes", f)
    if not callable(integers) or isinstance(integers, Expr):
        raise TypeError(f"computes expects a Python function, got {integers!r}")
    if f in _computations:
        raise ValueError(f"how {f!r} is computed is already recorded")
    _computations[f] = integers


def computation(f):
    _check_declared_function("computation", f)
    return _computations.get(f)
