/-
What a boolean expression of `python/nary` means: a proposition, or no
value, `Option Prop`. As for numbers, `none` is no value, and two meanings
are equal exactly when both have no value or both are the same proposition.

The comparisons `Lt`, `Gt`, `Le`, `Ge` and the connectives `And`, `Or`
follow two choices that issue #2 only proposes and the owner has not
confirmed. Each is marked "NOT CONFIRMED" below.
-/
import Nary.Number

noncomputable section
open Classical

namespace Nary

/-- What a `BoolKind` expression means: a proposition, or no value. -/
abbrev Boolean := Option Prop

/-- Whether a condition holds: it has a value and that value is true. A
condition with no value does not hold. -/
def Holds : Boolean → Prop
  | some p => p
  | none => False

/-- The constant `true`. -/
def true : Boolean := some True

/-- The constant `false`. -/
def false : Boolean := some False

/-- `Eq(a, b)`: `a` equals `b`. Has a value when both sides have one. -/
def Eq (a b : Number) : Boolean := do
  let x ← a
  let y ← b
  some (x = y)

/-- `Ne(a, b)`: `a` does not equal `b`. Has a value when both sides have
one. -/
def Ne (a b : Number) : Boolean := do
  let x ← a
  let y ← b
  some (x ≠ y)

/-- `Lt(a, b)`: `a < b`. Has a value when both sides have a value and both
values are real (imaginary part 0), so `Lt(0, I)` has no value; it is not
false.

NOT CONFIRMED: issue #2 proposes, but has not decided, that `<` has a value
only when both sides are real. -/
def Lt (a b : Number) : Boolean := do
  let x ← a
  let y ← b
  if x.im = 0 ∧ y.im = 0 then some (x.re < y.re) else none

/-- `Le(a, b)`: `a ≤ b`. Has a value when both sides have real values.

NOT CONFIRMED: as for `Lt`. -/
def Le (a b : Number) : Boolean := do
  let x ← a
  let y ← b
  if x.im = 0 ∧ y.im = 0 then some (x.re ≤ y.re) else none

/-- `Gt(a, b)`: `a > b`, which is `b < a`. NOT CONFIRMED: as for `Lt`. -/
def Gt (a b : Number) : Boolean := Lt b a

/-- `Ge(a, b)`: `a ≥ b`, which is `b ≤ a`. NOT CONFIRMED: as for `Lt`. -/
def Ge (a b : Number) : Boolean := Le b a

/-- `Not(p)`. Has a value when `p` does. -/
def Not (p : Boolean) : Boolean := p.map (¬ ·)

/-- `And(p, q, ...)`, for any number of arguments. `And()` is `true`.

It is false as soon as one argument is false, even if another has no value;
otherwise it has no value if some argument has none; otherwise every
argument is true, and so is the result.

NOT CONFIRMED: issue #2 proposes, but has not decided, this rule (Kleene
logic: `false and <no value>` is `false`). -/
def And (args : List Boolean) : Boolean :=
  if ∃ p, some p ∈ args ∧ ¬ p then some False
  else if none ∈ args then none
  else some True

/-- `Or(p, q, ...)`, for any number of arguments. `Or()` is `false`.

It is true as soon as one argument is true, even if another has no value;
otherwise it has no value if some argument has none; otherwise every
argument is false, and so is the result.

NOT CONFIRMED: as for `And` (`true or <no value>` is `true`). -/
def Or (args : List Boolean) : Boolean :=
  if ∃ p, some p ∈ args ∧ p then some True
  else if none ∈ args then none
  else some False

end Nary
