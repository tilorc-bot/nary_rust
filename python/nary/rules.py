"""Rewrite rules, the facts ``unordered`` and ``flat``, and ``computes``, as
plain data.

A rule says that one expression may be replaced by another. It is written
with the ordinary functions and operators, with ``rule``:

- ``rule(pattern, replacement, when=None, name=None)`` checks the rule and
  returns it as a ``Rule``. It is not recorded anywhere: a set of rules is
  an ordinary Python list of them, such as ``nary.arithmetic_rules.rules``.
- Every symbol in a rule is a variable: it stands for any expression of its
  kind, including one with no value. There is no list of variables. A
  declared constant such as ``pi`` or ``I`` stands for itself.
- A Python value as the replacement, such as the ``1`` of ``rule(a / a, 1)``,
  becomes a literal of the pattern's kind, the way ``x + 1`` converts ``1``.
- ``when=`` is a ``BoolKind`` expression. The rule may be applied only where
  it is known to hold.
- ``computed(e)``, only in the replacement, stands for the literal whose
  value is ``e`` worked out with Python integers when the rule is applied:
  ``rule(m + n, computed(m + n))`` turns ``Add(2, 3)`` into ``5``. ``e`` may
  contain only symbols, literals and functions recorded with ``computes``.
  Every symbol in it is a *literal variable* of the rule: it matches only a
  literal, and the rule is claimed only for integer values of it.
  ``Rule.literal_variables`` lists them.

A rule claims, following issue #2: wherever its condition holds and every
erased variable has a value, the pattern and the replacement both have no
value or both have the same value. A variable is erased when it is in the
pattern and not in the replacement, as ``a`` is in ``a * 0 -> 0``:
``log(0) * 0`` has no value, so that rule is only claimed where ``a`` has
one. ``Rule.erased`` lists those variables, and nothing more is derived from
it. It does not cover every rule that needs a condition: a rule can keep
every variable and still lose a partial function, as ``exp(log(a)) -> a``
loses ``log`` and is wrong at ``a = 0``. Such a condition is written with
``when=``.

    >>> from nary import BoolKind, Ne, NumberKind
    >>> from nary.logic import Not
    >>> from nary.rules import rule
    >>> a, p = NumberKind("a"), BoolKind("p")
    >>> r = rule(a / a, 1, when=Ne(a, 0))
    >>> r
    Rule(Mul(a, Pow(a, -1)), 1, when=Ne(a, 0))
    >>> r.pattern, r.replacement, r.condition, r.name
    (Mul(a, Pow(a, -1)), 1, Ne(a, 0), None)
    >>> r.variables, r.erased
    ((a,), (a,))
    >>> rule(Not(Not(p)), p, name="double negation")
    Rule(Not(Not(p)), p, name='double negation')
    >>> rule(a + 0, a + NumberKind("b"))
    Traceback (most recent call last):
        ...
    ValueError: every symbol of a rule must appear in its pattern, but b is in the replacement only
    >>> from nary.rules import computed
    >>> m, n = NumberKind("m"), NumberKind("n")
    >>> r = rule(m * a + n * a, computed(m + n) * a, name="collect")
    >>> r.replacement, r.literal_variables, r.erased
    (Mul(computed(Add(m, n)), a), (m, n), ())

Two facts about a function are recorded, next to the rules, because each is
a claim about what the function means that needs a proof, as a rule does.
They are not rules: applied as rewrites they would never stop. A matcher
would use them while matching.

- ``unordered(f)``: the order of ``f``'s arguments does not change its
  value, so ``Add(a, b, c)`` is ``Add(c, a, b)``. ``f`` must be a declared
  function whose positions all have the same kind, with no position that
  accepts only a symbol.
- ``flat(f)``: an ``f`` directly inside an ``f`` can be merged into it, so
  ``Add(a, Add(b, c))`` is ``Add(a, b, c)``. ``f`` must be a declared
  function that takes any number of arguments (``rest=``) of the kind it
  returns, and no other arguments.
- ``is_unordered(f)`` and ``is_flat(f)`` tell whether the fact is recorded.
  Each fact can be recorded once for each function.

A third declaration says what a function does on integers, for
``computed(...)``. It is not a claim that needs a proof: that Python's
integer ``+`` and ``*`` agree with Lean's on ``ℤ`` is taken on trust.

- ``computes(f, integers)``: ``integers`` is a Python function that is given
  the integer values of the arguments of ``f`` and returns the integer value
  of ``f`` applied to them, as in
  ``computes(Mul, lambda *integers: math.prod(integers))``. It can be
  recorded once for each function, and ``computation(f)`` returns it, or
  ``None``. ``nary.lean`` has the matching Lean spelling on ``ℤ``.

Refused, each with an error: a pattern that is not an expression or is a
bare symbol; a replacement of another kind than the pattern; a condition
that is not a ``BoolKind`` expression; a symbol in the replacement or the
condition that is not in the pattern; two symbols with the same name and
different kinds in one rule; ``computed`` in the pattern or the condition;
inside ``computed(...)``, anything but symbols, literals and applications
of functions recorded with ``computes``. A rule that contains a ``Lambda``
anywhere is refused for now: a variable bound by a lambda is not a variable
of the rule, and how such rules are written and matched has not been
designed.

Not here: rules are applied by ``nary.rewriting``, and ``nary.lean`` writes
a rule's claim as a Lean statement. Nothing decides a condition. The rules
about numbers are the list ``nary.arithmetic_rules.rules``.

The module is imported as ``nary.rules``; its names are not re-exported
from ``nary``.
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

# The declared functions recorded with unordered() and with flat().
_unordered = set()
_flat = set()
# The Python function recorded with computes() for each declared function.
_computations = {}

# A way of writing rules, not a mathematical function: computed(e) in a
# replacement is the literal whose value is e, worked out by the engine with
# Python integers. Applied to literals it is a literal, so its domain is
# true. It has no Lean definition; nary.lean prints it, in a rule, as Nary.lit
# applied to integer arithmetic.
computed = declare_function("computed", NumberKind, returns=NumberKind, domain=true)


def _subexpressions(e):
    """Every subexpression of ``e``, ``e`` first, then the head and the
    arguments of an application from left to right."""
    stack = [e]
    while stack:
        e = stack.pop()
        yield e
        if e.head is not None:
            stack.extend(reversed((e.head, *e.args)))


def _symbols(e):
    """The symbols of ``e``, each once, in order of first appearance.
    Refuses a lambda."""
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
    """The symbols of ``e``, the argument of a ``computed(...)``, after
    checking that the engine can compute ``e`` from integers."""
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
    """A rewrite rule: ``pattern`` may be replaced by ``replacement`` where
    ``condition`` holds (``None`` means everywhere) and every variable in
    ``erased`` has a value.

    ``variables`` are the symbols of the pattern, in order of first
    appearance, and ``erased`` those of them that are not in the
    replacement. ``literal_variables`` are those that appear inside a
    ``computed(...)``, in order of first appearance there; they match only
    literals. ``rule(...)`` builds one.
    """

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
        # Two symbols with one name and different kinds are different
        # variables that print the same.
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
    """Check and return the rule ``pattern -> replacement``.

    ``pattern`` is an expression that is not a bare symbol, and
    ``replacement`` an expression of the same kind, or a Python value that
    becomes a literal of that kind. Every symbol is a variable, and every
    symbol of the replacement and of ``when`` must be in the pattern.
    ``when`` is ``None`` or a ``BoolKind`` expression: the rule may be
    applied only where it is known to hold. ``name`` is ``None`` or a
    ``str``. A rule that contains a ``Lambda`` is refused for now.
    ``computed(...)`` may appear in the replacement only; every symbol
    inside it matches only a literal.
    """
    return Rule(pattern, replacement, when=when, name=name)


def _is_declared_function(e):
    """Whether ``e`` is a declared function: a constant of a function kind."""
    return isinstance(e, Expr) and e.is_constant and e.kind.inputs is not None


def _check_declared_function(caller, f):
    if not _is_declared_function(f):
        raise TypeError(f"{caller} expects a declared function, got {f!r}")


def unordered(f):
    """Record that the order of the arguments of the declared function ``f``
    does not change its value. Every position of ``f`` must have the same
    kind and accept any expression of it. It can be recorded once."""
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
    """Record that an application of the declared function ``f`` directly
    inside another can be merged into it. ``f`` must take any number of
    arguments (``rest=``) of the kind it returns, and no other arguments.
    It can be recorded once."""
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
    """Whether ``unordered(f)`` has been recorded."""
    _check_declared_function("is_unordered", f)
    return f in _unordered


def is_flat(f):
    """Whether ``flat(f)`` has been recorded."""
    _check_declared_function("is_flat", f)
    return f in _flat


def computes(f, integers):
    """Record that ``f`` applied to literals is computed by the Python
    function ``integers``, which is given their integer values and returns
    an integer. Used for ``computed(...)``. It can be recorded once."""
    _check_declared_function("computes", f)
    if not callable(integers) or isinstance(integers, Expr):
        raise TypeError(f"computes expects a Python function, got {integers!r}")
    if f in _computations:
        raise ValueError(f"how {f!r} is computed is already recorded")
    _computations[f] = integers


def computation(f):
    """The Python function recorded with ``computes(f, ...)``, or ``None``."""
    _check_declared_function("computation", f)
    return _computations.get(f)
