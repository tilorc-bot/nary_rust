"""Identities: everything that holds for a function, listed in one place.

An identity says that two expressions both have no value or have the same
value. In an identity every symbol is a placeholder, as in a rule
(``nary.rules``): it stands for any one expression of its kind. By
convention the name of a placeholder ends in one underscore (``a_``), or in
two (``s__``) for one that stands for any run of consecutive arguments,
including none. The two underscores are what make a placeholder stand for
a run of arguments; listing the identity checks that such a placeholder
sits only at a position that takes any number of arguments.

A generic identity is stated once, for any function, with
``declare_identity(name, left, right, params=(), normal=None)``. It is
written with placeholders of the kind ``PatternKind`` (and function
placeholders taking any number of them), declared here as an ordinary
kind: the core accepts a ``PatternKind`` expression only at a
``PatternKind`` position, which is all these trees need. The head of
``left`` is a function placeholder, ``f`` below; it is filled with the
function the identity is listed for. The placeholders in ``params`` are
filled where the identity is listed, by calling it, as in ``identity(0)``;
the parameter of ``inverse`` and ``repeated`` is an expression in the
identity's own placeholder ``a``, tied to it by name. ``e`` in
``inverse``, which is not in its left side, is the parameter of
``identity`` and is filled from the ``identity(e)`` listed in the same
block (``inverse`` is refused in a block without one). ``normal=`` is
recorded as data and nothing uses it yet. The generic identities declared
here (``f(s, f(t), u)`` is ``f_(s__, f_(t__), u__)``):

    associative   f(s, f(t), u) = f(s, t, u)
    singleton     f(a) = a
    identity(e)   f(s, e, t) = f(s, t)
    idempotent    f(s, a, t, a, u) = f(s, a, t, u)
    absorbing(z)  f(s, z, t) = z
    commutative   f(s, a, t, b, u) = f(s, b, t, a, u)    normal=Sorted
    distributive(g)  f(a, g(b, c)) = g(f(a, b), f(a, c))
    inverse(i)    f(a, i) = e, with e from identity(e)
    repeated(r)   f(a, a) = r

``declare_identities(F, items)`` is the one place where everything that
holds for the declared function ``F`` is listed: generic identities, called
with their parameters if they have any (and with ``when=`` if they hold
only where a condition does), and specific identities, each
``Equal(left, right, when=None, name=None)`` whose ``left`` is an
application of ``F``. ``singleton`` is not listed: it is added after
``associative`` for a block that lists that, and is stated and proved like
the others. Listing a generic identity fills ``f`` with ``F``, the
parameters with what it was called with (a Python value becomes a literal
of the kind of ``F``'s arguments) and every other placeholder with a symbol
of the same name of the kind of its position, and checks the result with
the ordinary kind checks, so a listing that makes no sense is refused when
the block is declared. A second block for the same function is refused.
``identities(F)`` returns the block as ``Identity`` records, each named
after its Lean statement: ``<function>_<identity>`` for a generic one
(``add_associative``, ``mul_absorbing``), the ``name=`` of an ``Equal``, or
else a name derived from its left side (``derived_name``: ``sin(0)`` gives
``sin_0``); and each with the listed item as an expression of the kind
``IdentityKind``: the generic identity applied to its parameters (a version
of it declared once for each combination of kinds), or the ``Equal``.

    >>> from nary import Add, NumberKind
    >>> from nary.identities import associative, identities
    >>> associative.definition
    Equal(f_(s__, f_(t__), u__), f_(s__, t__, u__))
    >>> [i.name for i in identities(Add)][:4]
    ['add_associative', 'add_singleton', 'add_commutative', 'add_identity']
    >>> i = identities(Add)[3]
    >>> i.item, i.lhs, i.rhs
    (identity(0), Add(s__, 0, t__), Add(s__, t__))
    >>> from nary.identities import declare_identities
    >>> from nary._core import declare_function
    >>> P = declare_function("P", NumberKind, NumberKind, returns=NumberKind)
    >>> declare_identities(P, [associative])
    Traceback (most recent call last):
        ...
    TypeError: associative cannot be listed for P: P takes 2 arguments, got 1
    >>> declare_identities(Add, [])
    Traceback (most recent call last):
        ...
    ValueError: the identities of Add are already declared

The identities do not rewrite anything themselves. ``nary.rules`` turns a
block into the facts and rules that ``nary.rewriting`` applies, and
``lean/generate_rules.py`` writes one Lean statement for each listed
identity. The module is imported as ``nary.identities``; its names
(``PatternKind`` and ``IdentityKind`` among them) are not re-exported from
``nary``.
"""

from . import _core
from ._core import Expr, FunctionKind, declare_kind
from .kinds import BoolKind

__all__ = [
    "Equal", "GenericIdentity", "Identity", "IdentityKind", "PatternKind",
    "declare_identities", "declare_identity", "identities", "is_equal", "lists",
    "absorbing", "associative", "commutative", "distributive", "idempotent", "identity",
    "inverse", "repeated", "singleton", "derived_name",
]

# The kind of the trees of the generic identities, and the kind of an
# identity (an Equal, or a generic identity listed for a function).
PatternKind = declare_kind("PatternKind")
IdentityKind = declare_kind("IdentityKind")

# The placeholders of the generic identities. A function placeholder takes
# any number of PatternKind arguments.
PatternFunction = FunctionKind((), PatternKind, rest=PatternKind)
f, g = PatternFunction("f_"), PatternFunction("g_")
a, b, c, e, i, r, z = (PatternKind(name + "_") for name in "abceirz")
s, t, u = (PatternKind(name + "__") for name in "stu")

# The function named "Equal" for each kind, declared the first time it is
# needed: it takes the two sides, of that kind, and at most one condition.
_equal_functions = {}
# The name given to an Equal with name=.
_names = {}


def Equal(lhs, rhs, when=None, name=None):
    """The identity ``lhs = rhs``, where ``when`` holds: an expression of
    the kind ``IdentityKind``. ``rhs`` is of the kind of ``lhs``, or a
    Python value that becomes a literal of it; ``when`` is ``None`` or a
    ``BoolKind`` expression. ``name`` is the name of the identity
    (``pow_one``); without it, ``declare_identities`` derives one from the
    left side."""
    if not isinstance(lhs, Expr):
        raise TypeError(f"the left side of an identity must be an expression, got {lhs!r}")
    kind = lhs.kind
    if kind not in _equal_functions:
        _equal_functions[kind] = _core.declare_function(
            "Equal", kind, kind, rest=BoolKind, returns=IdentityKind, names=("lhs", "rhs")
        )
    result = _equal_functions[kind](lhs, rhs, *(() if when is None else (when,)))
    if name is not None:
        if not isinstance(name, str) or not name.isidentifier():
            raise ValueError(f"the name of an identity must be an identifier, got {name!r}")
        if _names.setdefault(result, name) != name:
            raise ValueError(f"{result!r} is already named {_names[result]}")
    return result


def is_equal(e):
    """Whether ``e`` was made by ``Equal``."""
    if not (isinstance(e, Expr) and e.head is not None and e.head.is_constant):
        return False
    inputs = e.head.kind.inputs
    return bool(inputs) and _equal_functions.get(inputs[0]) is e.head


def _sides(identity):
    """The left side, right side and condition (or ``None``) of an
    ``Equal``."""
    lhs, rhs, *when = identity.args
    return lhs, rhs, (when[0] if when else None)


def _symbols(e):
    """The symbols of ``e``, each once, in order of first appearance."""
    found = []
    stack = [e]
    while stack:
        e = stack.pop()
        if e.is_symbol and e not in found:
            found.append(e)
        if e.head is not None:
            stack.extend(reversed((e.head, *e.args)))
    return found


class _Refused(Exception):
    pass


class GenericIdentity:
    """A generic identity, as ``declare_identity`` returns it: the identity
    ``definition`` (an ``Equal`` of ``PatternKind`` trees), its
    ``function`` placeholder, its ``params``, the placeholders ``multi``
    that stand for a run of arguments (by the convention, those whose name
    ends in two underscores), ``given`` (each placeholder of the right side
    that is not in the left, with the generic identity whose parameter it
    is) and ``normal``.

    One without parameters is listed as it is; one with parameters is
    called with them first, as in ``identity(0)``, which gives what
    ``declare_identities`` lists (not an expression: the kinds of the
    parameters are only known once the function is)."""

    __slots__ = ("_constant", "_versions", "definition", "function", "given", "multi", "name",
                 "normal", "params")

    def __init__(self, name, definition, function, params, multi, given, normal):
        set_ = object.__setattr__
        for attribute, value in (
            ("name", name), ("definition", definition), ("function", function),
            ("params", params), ("multi", multi), ("given", given), ("normal", normal),
            # The expression listed for each combination of the kinds of
            # the parameters: a constant, or a function declared once for
            # each combination, the way nary.functions declares Lambda.
            ("_constant", None if params else _core.declare_constant(name, IdentityKind)),
            ("_versions", {}),
        ):
            set_(self, attribute, value)

    def __setattr__(self, attribute, value):
        raise AttributeError("a GenericIdentity cannot be changed")

    def __call__(self, *values, when=None):
        if not self.params:
            raise TypeError(f"{self.name} takes no parameters, so it is listed without calling it")
        if len(values) != len(self.params):
            raise TypeError(
                f"{self.name} takes {len(self.params)} parameter(s) "
                f"({', '.join(p.name for p in self.params)}), got {len(values)}"
            )
        return _Listing(self, values, when)

    def _item(self, values):
        """The expression of kind ``IdentityKind`` that lists this identity
        with the parameters ``values`` (expressions)."""
        if not self.params:
            return self._constant
        kinds = tuple(v.kind for v in values)
        if kinds not in self._versions:
            self._versions[kinds] = _core.declare_function(
                self.name, *kinds, returns=IdentityKind,
                names=tuple(p.name.rstrip("_") for p in self.params),
            )
        return self._versions[kinds](*values)

    def __repr__(self):
        return self.name


class _Listing:
    """A generic identity called with its parameters, waiting for
    ``declare_identities`` to know the kinds."""

    __slots__ = ("generic", "values", "when")

    def __init__(self, generic, values, when=None):
        self.generic, self.values, self.when = generic, values, when

    def __repr__(self):
        when = () if self.when is None else (f"when={self.when!r}",)
        return f"{self.generic.name}({', '.join((*map(repr, self.values), *when))})"


# The generic identity whose parameter each placeholder is (e for identity).
_parameter_of = {}


def declare_identity(name, left, right, params=(), normal=None):
    """Declare the generic identity ``left = right`` and return it as a
    ``GenericIdentity``.

    ``left`` and ``right`` are ``PatternKind`` expressions, and every symbol
    in them is a placeholder; one whose name ends in two underscores
    (``s__``) stands for any run of arguments. The head of ``left`` must be
    a function placeholder; it is filled with the function the identity is
    listed for. ``params`` are placeholders filled where the identity is
    listed. Every placeholder of ``right`` must be in ``left``, be in
    ``params``, or be the parameter of a generic identity declared before (``e`` of
    ``identity``): it is then filled from that identity listed in the same
    block. ``normal`` is recorded as data; nothing uses it yet.
    """
    if not isinstance(name, str) or not name.isidentifier():
        raise ValueError(f"the name of an identity must be an identifier, got {name!r}")
    if not (isinstance(left, Expr) and left.kind is PatternKind):
        raise TypeError(
            f"a generic identity is written with PatternKind placeholders, so its left side "
            f"must be of kind PatternKind, got {left!r}"
        )
    definition = Equal(left, right)
    function = left.head
    if not (function is not None and function.is_symbol and function.kind.inputs is not None):
        raise ValueError(
            f"the left side of a generic identity must apply a function placeholder, got {left!r}"
        )
    in_left = _symbols(left)
    params = tuple(params)
    given = {}
    for p in _symbols(right):
        if p not in in_left and p not in params:
            if p not in _parameter_of:
                raise ValueError(
                    f"every placeholder of {name} must be in its left side or be the parameter "
                    f"of a generic identity, but {p!r} is neither"
                )
            given[p] = _parameter_of[p]
    multi = tuple(p for p in in_left if p.kind is PatternKind and p.name.endswith("__"))
    for p in params:
        if not (isinstance(p, Expr) and p in _symbols(definition)) or p == function or p in multi:
            raise ValueError(
                f"a parameter of {name} must be a placeholder of the identity other than "
                f"{function!r} and not a multi-argument placeholder, got {p!r}"
            )
    generic = GenericIdentity(name, definition, function, params, multi, given, normal)
    for p in params:
        _parameter_of.setdefault(p, generic)
    return generic


def _fill(e, filled, kinds, expected, multi):
    """``e`` with the placeholders in ``filled`` replaced, and every other
    placeholder replaced by the symbol of its name of the kind ``expected``
    at its position (or its own kind where that is not ``PatternKind``),
    rebuilt from the leaves with the ordinary kind checks. ``kinds`` records
    the kind each name got, and the same name may not get two. A
    placeholder in ``multi`` may only sit at a ``rest=`` position."""
    if e in filled:
        return filled[e]
    if e.is_symbol:
        kind = kinds.get(e.name)
        if kind is None:
            kind = expected if e.kind is PatternKind and expected is not None else e.kind
            kinds[e.name] = kind
        elif expected is not None and kind is not expected:
            raise _Refused(f"the placeholder {e.name} would be both {kind!r} and {expected!r}")
        return kind(e.name)
    if e.head is None:
        return e
    head = _fill(e.head, filled, kinds, None, multi)
    inputs = head.kind.inputs or ()
    rest = head.kind.rest
    args = []
    for position, arg in enumerate(e.args):
        position_kind = inputs[position] if position < len(inputs) else rest
        args.append(_fill(arg, filled, kinds, position_kind, multi))
    try:
        result = head(*args)
    except TypeError as error:
        raise _Refused(str(error)) from None
    for position, arg in enumerate(e.args):
        if arg in multi and position < len(inputs):
            raise _Refused(
                f"{head!r} cannot take the multi-argument placeholder {arg.name} at position "
                f"{position}, which takes exactly one argument"
            )
    return result


class Identity:
    """One identity listed for ``function``: ``lhs = rhs`` where ``when``
    holds (``None`` means everywhere). ``name`` is
    ``<function>_<identity>``, ``item`` the listed item as an expression of
    kind ``IdentityKind``, and ``generic`` the ``GenericIdentity`` it
    instantiates, or ``None`` for a specific identity."""

    __slots__ = ("function", "generic", "item", "lhs", "name", "rhs", "when")

    def __init__(self, name, function, item, generic, lhs, rhs, when):
        set_ = object.__setattr__
        for attribute, value in (
            ("name", name), ("function", function), ("item", item), ("generic", generic),
            ("lhs", lhs), ("rhs", rhs), ("when", when),
        ):
            set_(self, attribute, value)

    def __setattr__(self, attribute, value):
        raise AttributeError("an Identity cannot be changed")

    def __repr__(self):
        when = f" when {self.when!r}" if self.when is not None else ""
        return f"<identity {self.name}: {self.lhs!r} = {self.rhs!r}{when}>"


def _argument_kind(function):
    """The kind of the arguments of ``function``: of its ``rest=``
    position, else of its first."""
    kind = function.kind
    return kind.rest if kind.rest is not None else (kind.inputs or (None,))[0]


def _converted(function, values):
    """The parameters ``values`` as expressions: a Python value becomes a
    literal of the kind of ``function``'s arguments."""
    converted = []
    for value in values:
        if isinstance(value, Expr):
            converted.append(value)
            continue
        kind = _argument_kind(function)
        if isinstance(value, str) or kind is None:
            raise _Refused(f"{value!r} is not an expression")
        try:
            converted.append(kind(value))
        except (TypeError, ValueError) as error:
            raise _Refused(str(error)) from None
    return converted


def _instance(function, item, block):
    """The ``Identity`` that the generic identity ``item`` (a
    ``GenericIdentity`` or one called with its parameters) gives for
    ``function``, checked with the ordinary kind checks. ``block`` maps
    each generic identity listed in the same block to its parameters, for
    the placeholders the identity takes from another (``e`` of
    ``identity`` for ``inverse``)."""
    gen = item.generic if isinstance(item, _Listing) else item
    when = item.when if isinstance(item, _Listing) else None
    try:
        if gen.params and not isinstance(item, _Listing):
            raise _Refused(
                f"it takes the parameter(s) {', '.join(p.name for p in gen.params)}: list "
                f"{gen.name}(...)"
            )
        converted = block[item]
        filled = {gen.function: function, **dict(zip(gen.params, converted))}
        for p, other in gen.given.items():
            source = next((k for k in block if _generic(k) is other), None)
            if source is None:
                raise _Refused(f"it needs {other.name}({p.name}) listed in the same block")
            filled[p] = block[source][other.params.index(p)]
        # A placeholder in a parameter or in when= is the placeholder of
        # the identity of the same name.
        names = {p.name for p in _symbols(gen.definition)} - {p.name for p in filled}
        kinds = {}
        for value in [*converted, *(() if when is None else (when,))]:
            for p in _symbols(value) if isinstance(value, Expr) else ():
                if p.kind.inputs is not None:
                    continue
                if p.name not in names:
                    raise _Refused(f"{p.name} is not a placeholder of {gen.name}")
                if kinds.setdefault(p.name, p.kind) is not p.kind:
                    raise _Refused(f"the placeholder {p.name} would be two kinds")
        left, right, _ = _sides(gen.definition)
        lhs = _fill(left, filled, kinds, None, gen.multi)
        rhs = _fill(right, filled, kinds, lhs.kind, gen.multi)
        if lhs.kind is PatternKind:
            raise _Refused(f"it gives {lhs!r}, of the kind PatternKind")
        if rhs.kind is not lhs.kind:
            raise _Refused(f"its right side {rhs!r} is not of the kind {lhs.kind!r} of {lhs!r}")
    except _Refused as why:
        raise TypeError(f"{item!r} cannot be listed for {function!r}: {why}") from None
    return Identity(
        f"{function.name.lower()}_{gen.name}", function, gen._item(converted), gen, lhs, rhs,
        when,
    )


def _generic(item):
    return item.generic if isinstance(item, _Listing) else item


def _token(e):
    """The part of a derived name that stands for ``e``."""
    if e.is_literal:
        if type(e.value) is not int:
            raise ValueError(f"no name can be derived for the literal {e!r}: give name=")
        return str(e.value) if e.value >= 0 else f"neg{-e.value}"
    if e.head is None:
        return (e.name.rstrip("_") or e.name).lower()
    return "_".join([_token(e.head), *map(_token, e.args)])


def derived_name(function, lhs):
    """The name of an ``Equal`` listed for ``function`` without ``name=``:
    ``lhs`` written in prefix order, each function and constant by its name
    in lower case, each placeholder by its name without the underscores and
    each integer by its digits (``neg`` before a negative one), joined by
    underscores: ``sin(0)`` gives ``sin_0`` and ``sin(Mul(-1, a_))`` gives
    ``sin_mul_neg1_a``. Another literal has no name: give ``name=``."""
    return _token(lhs)


def _specific(function, identity):
    """The ``Identity`` of ``Equal(lhs, rhs, when, name)``."""
    if not is_equal(identity):
        raise TypeError(
            f"an identity listed for {function!r} is a generic identity, or "
            f"Equal(left, right, when=None, name=None), got {identity!r}"
        )
    lhs, rhs, when = _sides(identity)
    if lhs.head != function:
        raise ValueError(
            f"{identity!r} is listed under {function!r}, but its left side does not apply "
            f"{function!r}: an identity is listed under the function at the top of its left side"
        )
    in_left = _symbols(lhs)
    for p in _symbols(rhs) + (_symbols(when) if when is not None else []):
        if p not in in_left:
            raise ValueError(
                f"every placeholder of {identity!r} must be in its left side, but {p!r} is not"
            )
    name = _names.get(identity) or derived_name(function, lhs)
    return Identity(name, function, identity, None, lhs, rhs, when)


# The block of each function: a tuple of Identity records, and the set of
# the generic identities it lists.
_blocks = {}
_listed = {}


def declare_identities(function, items):
    """List everything that holds for the declared function ``function``:
    generic identities (called with their parameters, if any) and
    ``Equal(left, right, when=None, name=None)``. Each is checked; a listing
    that makes no sense is refused, and so is a second block for the same
    function. ``singleton`` is added after ``associative`` when the block
    lists it (it is not written in the blocks; its instance is still
    stated and proved)."""
    if not (isinstance(function, Expr) and function.is_constant and function.kind.inputs is not None):
        raise TypeError(f"declare_identities expects a declared function, got {function!r}")
    if function in _blocks:
        raise ValueError(f"the identities of {function!r} are already declared")
    items = list(items)
    if associative in items and singleton not in items:
        items.insert(items.index(associative) + 1, singleton)
    params = {}
    for item in items:
        if isinstance(item, (GenericIdentity, _Listing)):
            try:
                params[item] = _converted(function, getattr(item, "values", ()))
            except _Refused as why:
                raise TypeError(f"{item!r} cannot be listed for {function!r}: {why}") from None
    block = []
    for item in items:
        if isinstance(item, (GenericIdentity, _Listing)):
            block.append(_instance(function, item, params))
        else:
            block.append(_specific(function, item))
    names = [i.name for i in block]
    for name in names:
        if names.count(name) > 1:
            raise ValueError(f"two identities of {function!r} are named {name}")
    _blocks[function] = tuple(block)
    _listed[function] = frozenset(i.generic for i in block if i.generic is not None)


def identities(function):
    """The identities listed for ``function``, as a list of ``Identity``
    records in the order listed; empty if none were declared."""
    return list(_blocks.get(function, ()))


def lists(function, generic_identity):
    """Whether the block of ``function`` lists ``generic_identity``, such as
    ``associative``."""
    return generic_identity in _listed.get(function, ())


# The generic identities. Sorted is only a name for the normal form that
# commutative would sort arguments into; nothing uses it yet.
Sorted = "Sorted"

associative  = declare_identity("associative",  f(s, f(t), u),      f(s, t, u))
singleton    = declare_identity("singleton",    f(a),               a)
identity     = declare_identity("identity",     f(s, e, t),         f(s, t),           params=(e,))
idempotent   = declare_identity("idempotent",   f(s, a, t, a, u),   f(s, a, t, u))
absorbing    = declare_identity("absorbing",    f(s, z, t),         z,                 params=(z,))
commutative  = declare_identity("commutative",  f(s, a, t, b, u),   f(s, b, t, a, u),  normal=Sorted)
distributive = declare_identity("distributive", f(a, g(b, c)),      g(f(a, b), f(a, c)), params=(g,), normal=None)
inverse      = declare_identity("inverse",      f(a, i),            e,                 params=(i,))
repeated     = declare_identity("repeated",     f(a, a),            r,                 params=(r,))
