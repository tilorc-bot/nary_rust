import Mathlib.Analysis.SpecialFunctions.Complex.Log
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic

noncomputable section
open Classical

namespace Nary

abbrev Number := Option ℂ

def lit (n : ℤ) : Number := some (n : ℂ)

def rat (q : ℚ) : Number := some (q : ℂ)

def pi : Number := some (Real.pi : ℂ)

def E : Number := some (Complex.exp 1)

def I : Number := some Complex.I

def Add (args : List Number) : Number := (args.mapM id).map List.sum

def Mul (args : List Number) : Number := (args.mapM id).map List.prod

def withDomain (domain : ℂ → Prop) (f : ℂ → ℂ) (a : Number) : Number :=
  a.bind fun z => if domain z then some (f z) else none

def withDomain₂ (domain : ℂ → ℂ → Prop) (f : ℂ → ℂ → ℂ) (a b : Number) : Number := do
  let z ← a
  let w ← b
  if domain z w then some (f z w) else none

def powDomain (base exponent : ℂ) : Prop := base ≠ 0 ∨ 0 < exponent.re

def powTotal (base exponent : ℂ) : ℂ :=
  if base = 0 then 0 else Complex.exp (exponent * Complex.log base)

def Pow : Number → Number → Number := withDomain₂ powDomain powTotal

def sin (a : Number) : Number := a.map Complex.sin

def cos (a : Number) : Number := a.map Complex.cos

def tanDomain (z : ℂ) : Prop := Complex.cos z ≠ 0

def tan : Number → Number := withDomain tanDomain Complex.tan

def exp (a : Number) : Number := a.map Complex.exp

def logDomain (z : ℂ) : Prop := z ≠ 0

def log : Number → Number := withDomain logDomain Complex.log

def re (a : Number) : Number := a.map fun z => (z.re : ℂ)

end Nary
