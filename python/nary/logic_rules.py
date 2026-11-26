from ._identities import (
    absorbing, associative, commutative, declare_identities, idempotent, identity, involution,
)
from .logic import And, Not, Or, false, true

declare_identities(And, [
    associative, commutative, identity(true), absorbing(false), idempotent,
])
declare_identities(Or, [
    associative, commutative, identity(false), absorbing(true), idempotent,
])
declare_identities(Not, [involution])
