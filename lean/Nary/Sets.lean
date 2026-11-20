import Nary.Logic

noncomputable section
open Classical

namespace Nary

abbrev NumberSet := Option (Set ℂ)

def Reals : NumberSet := some {z | z.im = 0}

def Integers : NumberSet := some {z | ∃ n : ℤ, z = n}

def Contains (a : Number) (S : NumberSet) : Boolean := do
  let z ← a
  let s ← S
  some (z ∈ s)

def FiniteSet (args : List Number) : NumberSet :=
  (args.mapM id).map fun zs => {z | z ∈ zs}

def Union (args : List NumberSet) : NumberSet :=
  (args.mapM id).map fun ss => {z | ∃ s ∈ ss, z ∈ s}

-- Intersection [] is the set of all complex numbers.
def Intersection (args : List NumberSet) : NumberSet :=
  (args.mapM id).map fun ss => {z | ∀ s ∈ ss, z ∈ s}

theorem contains_reals (a : Number) : Contains a Reals = Eq (re a) a := by
  cases a with
  | none => rfl
  | some z => simp [Contains, Reals, Eq, re, Complex.ext_iff, eq_comm]

theorem lt_ne_none (a b : Number) :
    Lt a b ≠ none ↔ Holds (Contains a Reals) ∧ Holds (Contains b Reals) := by
  cases a <;> cases b <;> simp [Lt, Contains, Reals, Holds]

end Nary
