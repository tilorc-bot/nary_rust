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

end Nary
