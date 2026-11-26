/-
What a set expression of `python/nary/sets.py` means.

As for numbers and booleans, a set expression means a set of complex numbers
or no value, `Option (Set ℂ)`: `some s` is the set `s`, `none` is no value.
`FiniteSet(1/0)` has no value, because its argument has none. Every function
here is strict: if an argument has no value, neither does the result.

`Reals` and `Integers` are what "is real" and "is an integer" mean: `a` is
real when `Contains(a, Reals)` holds. The two theorems at the end tie this to
what is already defined: `Contains(a, Reals)` means the same as
`Eq(re(a), a)`, and `Lt(a, b)` has a value exactly when `a` and `b` are both
real.
-/
import Nary.Logic

noncomputable section
open Classical

namespace Nary

/-- What a `SetKind(NumberKind)` expression means: a set of complex numbers,
or no value. -/
abbrev NumberSet := Option (Set ℂ)

/-- The constant `Reals`: the complex numbers whose imaginary part is 0. -/
def Reals : NumberSet := some {z | z.im = 0}

/-- The constant `Integers`: the integers, as complex numbers. -/
def Integers : NumberSet := some {z | ∃ n : ℤ, z = n}

/-- `Contains(a, S)`: `a` is in `S`. Has a value when `a` and `S` have one. -/
def Contains (a : Number) (S : NumberSet) : Boolean := do
  let z ← a
  let s ← S
  some (z ∈ s)

/-- `FiniteSet(a, b, ...)`: the set of the arguments. `FiniteSet()` is the
empty set. Has a value when every argument has one. -/
def FiniteSet (args : List Number) : NumberSet :=
  (args.mapM id).map fun zs => {z | z ∈ zs}

/-- `Union(S, T, ...)`: the numbers in at least one of the sets. `Union()` is
the empty set. Has a value when every argument has one. -/
def Union (args : List NumberSet) : NumberSet :=
  (args.mapM id).map fun ss => {z | ∃ s ∈ ss, z ∈ s}

/-- `Intersection(S, T, ...)`: the numbers in every one of the sets.
`Intersection()` is the set of all complex numbers (every number is in each
of no sets). Has a value when every argument has one. -/
def Intersection (args : List NumberSet) : NumberSet :=
  (args.mapM id).map fun ss => {z | ∀ s ∈ ss, z ∈ s}

/-- `Contains(a, Reals)` means the same as `Eq(re(a), a)`: both have no value
when `a` has none, and otherwise both say that `a` is real. -/
theorem contains_reals (a : Number) : Contains a Reals = Eq (re a) a := by
  cases a with
  | none => rfl
  | some z => simp [Contains, Reals, Eq, re, Complex.ext_iff, eq_comm]

/-- `Lt(a, b)` has a value exactly when `a` and `b` have values and both are
in `Reals`. -/
theorem lt_ne_none (a b : Number) :
    Lt a b ≠ none ↔ Holds (Contains a Reals) ∧ Holds (Contains b Reals) := by
  cases a <;> cases b <;> simp [Lt, Contains, Reals, Holds]

end Nary
