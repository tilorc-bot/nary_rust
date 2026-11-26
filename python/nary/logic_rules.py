from ._identities import (
    associative, commutative, declare_identities, dominant, idempotent, identity, involution,
)
from .logic import And, Not, Or, false, true

declare_identities(And, [
    associative, commutative, identity(true), dominant(false), idempotent,
])
declare_identities(Or, [
    associative, commutative, identity(false), dominant(true), idempotent,
])
declare_identities(Not, [involution])
