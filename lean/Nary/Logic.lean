import Nary.Number

noncomputable section
open Classical

namespace Nary

abbrev Boolean := Option Prop

def Holds : Boolean → Prop
  | some p => p
  | none => False

def true : Boolean := some True

def false : Boolean := some False

def Eq (a b : Number) : Boolean := do
  let x ← a
  let y ← b
  some (x = y)

def Ne (a b : Number) : Boolean := do
  let x ← a
  let y ← b
  some (x ≠ y)

def Lt (a b : Number) : Boolean := do
  let x ← a
  let y ← b
  if x.im = 0 ∧ y.im = 0 then some (x.re < y.re) else none

def Le (a b : Number) : Boolean := do
  let x ← a
  let y ← b
  if x.im = 0 ∧ y.im = 0 then some (x.re ≤ y.re) else none

def Gt (a b : Number) : Boolean := Lt b a

def Ge (a b : Number) : Boolean := Le b a

def Not (p : Boolean) : Boolean := p.map (¬ ·)

def And (args : List Boolean) : Boolean :=
  if ∃ p, some p ∈ args ∧ ¬ p then some False
  else if none ∈ args then none
  else some True

def Or (args : List Boolean) : Boolean :=
  if ∃ p, some p ∈ args ∧ p then some True
  else if none ∈ args then none
  else some False

theorem holds_and (ps : List Boolean) : Holds (And ps) ↔ ∀ p ∈ ps, Holds p := by
  unfold And
  split_ifs with h₁ h₂
  · obtain ⟨p, hp, hn⟩ := h₁
    simp only [Holds, false_iff, not_forall]
    exact ⟨some p, hp, hn⟩
  · simp only [Holds, false_iff, not_forall]
    exact ⟨none, h₂, id⟩
  · simp only [Holds, true_iff]
    intro q hq
    cases q with
    | none => exact absurd hq h₂
    | some p => by_contra hn; exact h₁ ⟨p, hq, hn⟩

end Nary
