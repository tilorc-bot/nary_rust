"""Identities: everything that holds for a function, listed in one place.

An identity says that two expressions both have no value or have the same
value. It is written with holes, made by ``hole(kind, name, multi=False)``:
a hole stands for any one expression of its kind, and a multi-argument hole
(``multi=True``) for any run of consecutive arguments, including none. In
an identity a symbol stands for itself; only holes are placeholders.

A generic identity is stated once, for any function, with
``declare_identity(name, left, right, params=(), normal=None)``. The head
of ``left`` is a function hole, ``f`` below; it is filled with the function
the identity is listed for. The holes in ``params`` are filled where the
identity is listed: the declared identity is then applied to them, as in
``identity(NumberKind(0))``, which is an expression (of the generic kind
``AnyKind``), not a rule. ``normal=`` is recorded as data and nothing uses
it yet. The generic identities declared here:

    f(s, f(t), u) = f(s, t, u)              associative
    f(s, a, t, b, u) = f(s, b, t, a, u)     commutative   normal=Sorted
    f(a) = a                                singleton
    f(s, e, t) = f(s, t)                    identity(e)
    f(s, a, t, a, u) = f(s, a, t, u)        idempotent
    f(s, z, t) = z                          absorbing(z)
    f(a, g(b, c)) = g(f(a, b), f(a, c))     distributive(g)

``declare_identities(F, items)`` is the one place where everything that
holds for the declared function ``F`` is listed: generic identities, applied
to their parameters, and specific identities, each a pair
``(name, Equal(left, right, when=None))`` whose ``left`` is an application
of ``F``. Listing a generic identity fills ``f`` with ``F`` and the
parameters with what it is applied to, and checks the result with the
ordinary kind checks, so a listing that makes no sense is refused when the
block is declared. A second block for the same function is refused.
``identities(F)`` returns the block as ``Identity`` records, each named
``<function>_<identity>`` (``add_associative``, ``mul_absorbing``), the name
of its Lean statement.

    >>> from nary import Add, AnyKind, NumberKind, Pow, sin
    >>> from nary.identities import associative, generic, identities
    >>> generic(associative).definition
    Equal(?f(?s*, ?f(?t*), ?u*), ?f(?s*, ?t*, ?u*))
    >>> [i.name for i in identities(Add)][:4]
    ['add_associative', 'add_commutative', 'add_singleton', 'add_identity']
    >>> i = identities(Add)[3]
    >>> i.item, i.lhs, i.rhs
    (identity(0), Add(?s*, 0, ?t*), Add(?s*, ?t*))
    >>> from nary.identities import declare_identities
    >>> declare_identities(Pow, [associative])
    Traceback (most recent call last):
        ...
    TypeError: associative cannot be listed for Pow: Pow takes 2 arguments, got 1

The identities do not rewrite anything themselves. ``nary.rules`` turns a
block into the facts and rules that ``nary.rewriting`` applies, and
``lean/generate_rules.py`` writes one Lean statement for each listed
identity. The module is imported as ``nary.identities``; its names are not
re-exported from ``nary``.
"""

from . import _core
from ._core import AnyKind, Expr, FunctionKind, hole
from .kinds import BoolKind

__all__ = [
    "Equal", "GenericIdentity", "Identity", "declare_identities", "declare_identity",
    "generic", "hole", "identities", "is_equal", "lists",
    "absorbing", "associative", "commutative", "distributive", "idempotent", "identity",
    "singleton",
]

# The function holes and holes of the generic identities. ``f`` takes any
# number of arguments of any kind.
AnyFunction = FunctionKind((), AnyKind, rest=AnyKind)
f, g = hole(AnyFunction, "f"), hole(AnyFunction, "g")
a, b, c, e, z = (hole(AnyKind, name) for name in "abcez")
s, t, u = (hole(AnyKind, name, multi=True) for name in "stu")

# The function named "Equal" for each kind, declared the first time it is
# needed: it takes the two sides, of that kind, and at most one condition.
_equal_functions = {}


def Equal(lhs, rhs, when=None):
    """The identity ``lhs = rhs``, where ``when`` holds: an expression of
    the generic kind ``AnyKind``. ``rhs`` is of the kind of ``lhs``, or a
    Python value that becomes a literal of it; ``when`` is ``None`` or a
    ``BoolKind`` expression."""
    if not isinstance(lhs, Expr):
        raise TypeError(f"the left side of an identity must be an expression, got {lhs!r}")
    kind = lhs.kind
    if kind not in _equal_functions:
        _equal_functions[kind] = _core.declare_function(
            "Equal", kind, kind, rest=BoolKind, returns=AnyKind, names=("lhs", "rhs")
        )
    return _equal_functions[kind](lhs, rhs, *(() if when is None else (when,)))


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


def _holes(e):
    """The holes of ``e``, each once, in order of first appearance."""
    found = []
    stack = [e]
    while stack:
        e = stack.pop()
        if e.is_hole and e not in found:
            found.append(e)
        if e.head is not None:
            stack.extend(reversed((e.head, *e.args)))
    return found


def _symbols(e):
    stack, found = [e], []
    while stack:
        e = stack.pop()
        if e.is_symbol:
            found.append(e)
        if e.head is not None:
            stack.extend((e.head, *e.args))
    return found


class GenericIdentity:
    """What ``declare_identity`` records: the identity ``definition`` (an
    ``Equal``), its ``function`` hole, its ``params`` and ``normal``."""

    __slots__ = ("definition", "function", "name", "normal", "params")

    def __init__(self, name, definition, function, params, normal):
        set_ = object.__setattr__
        set_(self, "name", name)
        set_(self, "definition", definition)
        set_(self, "function", function)
        set_(self, "params", params)
        set_(self, "normal", normal)

    def __setattr__(self, attribute, value):
        raise AttributeError("a GenericIdentity cannot be changed")

    def __repr__(self):
        return f"<generic identity {self.name}: {self.definition!r}>"


# The generic identities, by the declared expression (a constant, or a
# function of the parameters).
_generic = {}


def declare_identity(name, left, right, params=(), normal=None):
    """Declare the generic identity ``left = right`` and return it as a
    declared expression of the generic kind ``AnyKind``: a constant if
    ``params`` is empty, otherwise a function that takes one argument for
    each hole in ``params``.

    The head of ``left`` must be a function hole; it is filled with the
    function the identity is listed for. ``params`` are holes of ``left``
    that are not multi-argument holes. Every hole of ``right`` must be in
    ``left``. ``normal`` is recorded as data; nothing uses it yet.
    """
    if not isinstance(name, str) or not name.isidentifier():
        raise ValueError(f"the name of an identity must be an identifier, got {name!r}")
    definition = Equal(left, right)
    function = left.head
    if not (function is not None and function.is_hole and function.kind.inputs is not None):
        raise ValueError(
            f"the left side of a generic identity must apply a function hole, got {left!r}"
        )
    in_left = _holes(left)
    for h in _holes(right):
        if h not in in_left:
            raise ValueError(f"every hole of {name} must be in its left side, but {h!r} is not")
    if _symbols(definition):
        raise ValueError(
            f"a generic identity is written with holes only, got the symbols "
            f"{_symbols(definition)!r} in {name}"
        )
    params = tuple(params)
    for p in params:
        if not (isinstance(p, Expr) and p in in_left and not p.is_multi_hole) or p == function:
            raise ValueError(
                f"a parameter of {name} must be a hole of its left side other than "
                f"{function!r} and not a multi-argument hole, got {p!r}"
            )
    if params:
        declared = _core.declare_function(
            name, *(AnyKind for _ in params), returns=AnyKind,
            names=tuple(p.name for p in params),
        )
    else:
        declared = _core.declare_constant(name, AnyKind)
    _generic[declared] = GenericIdentity(name, definition, function, params, normal)
    return declared


def _generic_of(item):
    """The generic identity that ``item`` lists, and what its parameters are
    filled with; ``(None, ())`` if it lists none."""
    if not isinstance(item, Expr):
        return None, ()
    if item in _generic:
        return _generic[item], ()
    if item.head is not None and item.head in _generic:
        return _generic[item.head], item.args
    return None, ()


def generic(e):
    """The ``GenericIdentity`` of a declared generic identity, or ``None``."""
    return _generic.get(e)


class _Refused(Exception):
    pass


def _fill(e, filled, kinds, expected):
    """``e`` with the holes in ``filled`` replaced, rebuilt from the leaves
    with the ordinary kind checks. A hole of kind ``AnyKind`` becomes a hole
    of the kind ``expected`` at its position; ``kinds`` records the kind
    each hole name got, and the same name may not get two."""
    if e in filled:
        return filled[e]
    if e.is_hole:
        kind = kinds.get(e.name)
        if kind is None:
            kind = expected if e.kind is AnyKind and expected is not None else e.kind
            kinds[e.name] = kind
        elif expected is not None and expected is not AnyKind and kind is not expected:
            raise _Refused(f"the hole ?{e.name} would be both {kind!r} and {expected!r}")
        return hole(kind, e.name, multi=e.is_multi_hole)
    if e.head is None:
        return e
    head = _fill(e.head, filled, kinds, None)
    inputs = head.kind.inputs or ()
    rest = head.kind.rest
    args = []
    for position, arg in enumerate(e.args):
        position_kind = inputs[position] if position < len(inputs) else rest
        args.append(_fill(arg, filled, kinds, position_kind))
    try:
        return head(*args)
    except TypeError as error:
        raise _Refused(str(error)) from None


class Identity:
    """One identity listed for ``function``: ``lhs = rhs`` where ``when``
    holds (``None`` means everywhere). ``name`` is
    ``<function>_<identity>``, ``item`` the expression as listed, and
    ``generic`` the declared generic identity it instantiates, or ``None``
    for a specific identity."""

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


def _instance(function, item):
    """The ``Identity`` that the generic identity ``item`` gives for
    ``function``, checked with the ordinary kind checks."""
    gen, values = _generic_of(item)
    declared = item if item in _generic else item.head
    filled = {gen.function: function, **dict(zip(gen.params, values))}
    kinds = {}
    left, right, _ = _sides(gen.definition)
    try:
        lhs = _fill(left, filled, kinds, None)
        rhs = _fill(right, filled, kinds, lhs.kind)
        if lhs.kind.generic:
            raise _Refused(f"it gives {lhs!r}, of the generic kind {lhs.kind!r}")
        if rhs.kind is not lhs.kind:
            raise _Refused(f"its right side {rhs!r} is not of the kind {lhs.kind!r} of {lhs!r}")
    except _Refused as why:
        raise TypeError(f"{item!r} cannot be listed for {function!r}: {why}") from None
    return Identity(
        f"{function.name.lower()}_{gen.name}", function, item, declared, lhs, rhs, None
    )


def _specific(function, item):
    """The ``Identity`` of the pair ``(name, Equal(lhs, rhs, when))``."""
    if not (isinstance(item, tuple) and len(item) == 2 and is_equal(item[1])):
        raise TypeError(
            f"an identity listed for {function!r} is a generic identity, or a pair "
            f"(name, Equal(left, right, when=None)), got {item!r}"
        )
    name, identity = item
    if not isinstance(name, str) or not name.isidentifier():
        raise ValueError(f"the name of an identity must be an identifier, got {name!r}")
    lhs, rhs, when = _sides(identity)
    if lhs.head != function:
        raise ValueError(
            f"{identity!r} is listed under {function!r}, but its left side does not apply "
            f"{function!r}: an identity is listed under the function at the top of its left side"
        )
    symbols = _symbols(identity)
    if symbols:
        raise ValueError(
            f"in an identity a symbol stands for itself, which nothing can use yet: "
            f"write {symbols[0]!r} in {identity!r} as a hole"
        )
    in_left = _holes(lhs)
    for h in _holes(rhs) + (_holes(when) if when is not None else []):
        if h not in in_left:
            raise ValueError(f"every hole of {identity!r} must be in its left side, but {h!r} is not")
    return Identity(f"{function.name.lower()}_{name}", function, identity, None, lhs, rhs, when)


# The block of each function: a tuple of Identity records, and the set of
# the generic identities it lists.
_blocks = {}
_listed = {}


def declare_identities(function, items):
    """List everything that holds for the declared function ``function``:
    generic identities applied to their parameters, and pairs
    ``(name, Equal(left, right, when=None))``. Each is checked; a listing
    that makes no sense is refused, and so is a second block for the same
    function."""
    if not (isinstance(function, Expr) and function.is_constant and function.kind.inputs is not None):
        raise TypeError(f"declare_identities expects a declared function, got {function!r}")
    if function.kind.generic:
        raise TypeError(f"declare_identities expects a function with a meaning, got {function!r}")
    if function in _blocks:
        raise ValueError(f"the identities of {function!r} are already declared")
    block = []
    for item in items:
        gen, _ = _generic_of(item)
        block.append(_instance(function, item) if gen is not None else _specific(function, item))
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

associative = declare_identity("associative", f(s, f(t), u), f(s, t, u))
commutative = declare_identity("commutative", f(s, a, t, b, u), f(s, b, t, a, u), normal=Sorted)
singleton = declare_identity("singleton", f(a), a)
identity = declare_identity("identity", f(s, e, t), f(s, t), params=(e,))
idempotent = declare_identity("idempotent", f(s, a, t, a, u), f(s, a, t, u))
absorbing = declare_identity("absorbing", f(s, z, t), z, params=(z,))
distributive = declare_identity(
    "distributive", f(a, g(b, c)), g(f(a, b), f(a, c)), params=(g,), normal=None
)
