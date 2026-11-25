"""Identities: everything that holds for a function, listed in one place.

An identity says that two expressions both have no value or have the same
value. In an identity every symbol is a placeholder, as in a rule
(``nary.rules``): it stands for any one expression of its kind. By
convention the name of a placeholder ends in one underscore (``a_``), or in
two (``s__``) for one that stands for any run of consecutive arguments,
including none. The convention is only for reading: which placeholders
stand for a run of arguments is given to ``declare_identity`` with
``multi=``, not inferred from the name.

A generic identity is stated once, for any function, with
``declare_identity(name, left, right, params=(), multi=(), normal=None)``.
It is written with placeholders of the kind ``PatternKind`` (and function
placeholders taking any number of them), declared here as an ordinary kind:
the core accepts a ``PatternKind`` expression only at a ``PatternKind``
position, which is all these trees need. The head of ``left`` is a
function placeholder, ``f_`` below; it is filled with the function the
identity is listed for. The placeholders in ``params`` are filled where the
identity is listed, by calling it, as in ``identity(0)``. A placeholder in
``multi`` may only sit at a position that takes any number of arguments,
which is checked when the identity is listed. ``normal=`` is recorded as
data and nothing uses it yet. The generic identities declared here:

    f_(s__, f_(t__), u__) = f_(s__, t__, u__)           associative
    f_(s__, a_, t__, b_, u__) = f_(s__, b_, t__, a_, u__) commutative  normal=Sorted
    f_(a_) = a_                                         singleton
    f_(s__, e_, t__) = f_(s__, t__)                     identity(e_)
    f_(s__, a_, t__, a_, u__) = f_(s__, a_, t__, u__)   idempotent
    f_(s__, z_, t__) = z_                               absorbing(z_)
    f_(a_, g_(b_, c_)) = g_(f_(a_, b_), f_(a_, c_))     distributive(g_)

``declare_identities(F, items)`` is the one place where everything that
holds for the declared function ``F`` is listed: generic identities, called
with their parameters if they have any, and specific identities, each a
pair ``(name, Equal(left, right, when=None))`` whose ``left`` is an
application of ``F``. Listing a generic identity fills ``f_`` with ``F``,
the parameters with what it was called with (a Python value becomes a
literal of the kind of ``F``'s arguments) and every other placeholder with
a symbol of the same name of the kind of its position, and checks the
result with the ordinary kind checks, so a listing that makes no sense is
refused when the block is declared. A second block for the same function
is refused. ``identities(F)`` returns the block as ``Identity`` records,
each named ``<function>_<identity>`` (``add_associative``,
``mul_absorbing``), the name of its Lean statement, and each with the
listed item as an expression of the kind ``IdentityKind``: the generic
identity applied to its parameters (a version of it declared once for each
combination of kinds), or the ``Equal``.

    >>> from nary import Add, NumberKind
    >>> from nary.identities import associative, identities
    >>> associative.definition
    Equal(f_(s__, f_(t__), u__), f_(s__, t__, u__))
    >>> [i.name for i in identities(Add)][:4]
    ['add_associative', 'add_commutative', 'add_singleton', 'add_identity']
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
    "singleton",
]

# The kind of the trees of the generic identities, and the kind of an
# identity (an Equal, or a generic identity listed for a function).
PatternKind = declare_kind("PatternKind")
IdentityKind = declare_kind("IdentityKind")

# The placeholders of the generic identities. A function placeholder takes
# any number of PatternKind arguments.
PatternFunction = FunctionKind((), PatternKind, rest=PatternKind)
f_, g_ = PatternFunction("f_"), PatternFunction("g_")
a_, b_, c_, e_, z_ = (PatternKind(name + "_") for name in "abcez")
s__, t__, u__ = (PatternKind(name + "__") for name in "stu")

# The function named "Equal" for each kind, declared the first time it is
# needed: it takes the two sides, of that kind, and at most one condition.
_equal_functions = {}


def Equal(lhs, rhs, when=None):
    """The identity ``lhs = rhs``, where ``when`` holds: an expression of
    the kind ``IdentityKind``. ``rhs`` is of the kind of ``lhs``, or a
    Python value that becomes a literal of it; ``when`` is ``None`` or a
    ``BoolKind`` expression."""
    if not isinstance(lhs, Expr):
        raise TypeError(f"the left side of an identity must be an expression, got {lhs!r}")
    kind = lhs.kind
    if kind not in _equal_functions:
        _equal_functions[kind] = _core.declare_function(
            "Equal", kind, kind, rest=BoolKind, returns=IdentityKind, names=("lhs", "rhs")
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
    ``function`` placeholder, its ``params``, the placeholders in ``multi``
    and ``normal``.

    One without parameters is listed as it is; one with parameters is
    called with them first, as in ``identity(0)``, which gives what
    ``declare_identities`` lists (not an expression: the kinds of the
    parameters are only known once the function is)."""

    __slots__ = ("_constant", "_versions", "definition", "function", "multi", "name",
                 "normal", "params")

    def __init__(self, name, definition, function, params, multi, normal):
        set_ = object.__setattr__
        for attribute, value in (
            ("name", name), ("definition", definition), ("function", function),
            ("params", params), ("multi", multi), ("normal", normal),
            # The expression listed for each combination of the kinds of
            # the parameters: a constant, or a function declared once for
            # each combination, the way nary.functions declares Lambda.
            ("_constant", None if params else _core.declare_constant(name, IdentityKind)),
            ("_versions", {}),
        ):
            set_(self, attribute, value)

    def __setattr__(self, attribute, value):
        raise AttributeError("a GenericIdentity cannot be changed")

    def __call__(self, *values):
        if not self.params:
            raise TypeError(f"{self.name} takes no parameters, so it is listed without calling it")
        if len(values) != len(self.params):
            raise TypeError(
                f"{self.name} takes {len(self.params)} parameter(s) "
                f"({', '.join(p.name for p in self.params)}), got {len(values)}"
            )
        return _Listing(self, values)

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

    __slots__ = ("generic", "values")

    def __init__(self, generic, values):
        self.generic, self.values = generic, values

    def __repr__(self):
        return f"{self.generic.name}({', '.join(map(repr, self.values))})"


def declare_identity(name, left, right, params=(), multi=(), normal=None):
    """Declare the generic identity ``left = right`` and return it as a
    ``GenericIdentity``.

    ``left`` and ``right`` are ``PatternKind`` expressions, and every symbol
    in them is a placeholder. The head of ``left`` must be a function
    placeholder; it is filled with the function the identity is listed for.
    ``params`` are placeholders of ``left`` filled where the identity is
    listed; ``multi`` are the placeholders of ``left`` that stand for any
    run of arguments (none of them a parameter). Every placeholder of
    ``right`` must be in ``left``. ``normal`` is recorded as data; nothing
    uses it yet.
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
    for p in _symbols(right):
        if p not in in_left:
            raise ValueError(
                f"every placeholder of {name} must be in its left side, but {p!r} is not"
            )
    multi = tuple(multi)
    for m in multi:
        if not (isinstance(m, Expr) and m in in_left and m.kind is PatternKind):
            raise ValueError(
                f"a multi-argument placeholder of {name} must be a PatternKind placeholder "
                f"of its left side, got {m!r}"
            )
    params = tuple(params)
    for p in params:
        if not (isinstance(p, Expr) and p in in_left) or p == function or p in multi:
            raise ValueError(
                f"a parameter of {name} must be a placeholder of its left side other than "
                f"{function!r} and not a multi-argument placeholder, got {p!r}"
            )
    return GenericIdentity(name, definition, function, params, multi, normal)


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


def _instance(function, item):
    """The ``Identity`` that the generic identity ``item`` (a
    ``GenericIdentity`` or one called with its parameters) gives for
    ``function``, checked with the ordinary kind checks."""
    gen, values = (item.generic, item.values) if isinstance(item, _Listing) else (item, ())
    try:
        if gen.params and not isinstance(item, _Listing):
            raise _Refused(
                f"it takes the parameter(s) {', '.join(p.name for p in gen.params)}: list "
                f"{gen.name}(...)"
            )
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
        filled = {gen.function: function, **dict(zip(gen.params, converted))}
        kinds = {}
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
        None,
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
    in_left = _symbols(lhs)
    for p in _symbols(rhs) + (_symbols(when) if when is not None else []):
        if p not in in_left:
            raise ValueError(
                f"every placeholder of {identity!r} must be in its left side, but {p!r} is not"
            )
    return Identity(f"{function.name.lower()}_{name}", function, identity, None, lhs, rhs, when)


# The block of each function: a tuple of Identity records, and the set of
# the generic identities it lists.
_blocks = {}
_listed = {}


def declare_identities(function, items):
    """List everything that holds for the declared function ``function``:
    generic identities (called with their parameters, if any) and pairs
    ``(name, Equal(left, right, when=None))``. Each is checked; a listing
    that makes no sense is refused, and so is a second block for the same
    function."""
    if not (isinstance(function, Expr) and function.is_constant and function.kind.inputs is not None):
        raise TypeError(f"declare_identities expects a declared function, got {function!r}")
    if function in _blocks:
        raise ValueError(f"the identities of {function!r} are already declared")
    block = []
    for item in items:
        if isinstance(item, (GenericIdentity, _Listing)):
            block.append(_instance(function, item))
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

associative = declare_identity(
    "associative", f_(s__, f_(t__), u__), f_(s__, t__, u__), multi=(s__, t__, u__)
)
commutative = declare_identity(
    "commutative", f_(s__, a_, t__, b_, u__), f_(s__, b_, t__, a_, u__),
    multi=(s__, t__, u__), normal=Sorted,
)
singleton = declare_identity("singleton", f_(a_), a_)
identity = declare_identity(
    "identity", f_(s__, e_, t__), f_(s__, t__), params=(e_,), multi=(s__, t__)
)
idempotent = declare_identity(
    "idempotent", f_(s__, a_, t__, a_, u__), f_(s__, a_, t__, u__), multi=(s__, t__, u__)
)
absorbing = declare_identity(
    "absorbing", f_(s__, z_, t__), z_, params=(z_,), multi=(s__, t__)
)
distributive = declare_identity(
    "distributive", f_(a_, g_(b_, c_)), g_(f_(a_, b_), f_(a_, c_)), params=(g_,), normal=None
)
