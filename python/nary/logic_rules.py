from .logic import And, Or, false, true
from .properties import declare_properties

declare_properties(
    And, is_associative=True, is_commutative=True, identity_element=true,
    absorbing_element=false, is_idempotent=True,
)
declare_properties(
    Or, is_associative=True, is_commutative=True, identity_element=false,
    absorbing_element=true, is_idempotent=True,
)
