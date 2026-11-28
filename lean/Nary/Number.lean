import Mathlib.Analysis.SpecialFunctions.Complex.Log
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic

noncomputable section
open Classical

namespace Nary

abbrev Number := Option ℂ

def lit (n : ℤ) : Number := some (n : ℂ)

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

def sinh (a : Number) : Number := a.map Complex.sinh

def cosh (a : Number) : Number := a.map Complex.cosh

def tanhDomain (z : ℂ) : Prop := Complex.cosh z ≠ 0

def tanh : Number → Number := withDomain tanhDomain Complex.tanh

def im (a : Number) : Number := a.map fun z => (z.im : ℂ)

def Abs (a : Number) : Number := a.map fun z => (‖z‖ : ℂ)

def argDomain (z : ℂ) : Prop := z ≠ 0

def arg : Number → Number := withDomain argDomain fun z => (Complex.arg z : ℂ)

def conjugate (a : Number) : Number := a.map (starRingEnd ℂ)

def sign (a : Number) : Number := a.map fun z => z / (‖z‖ : ℂ)

def realDomain (z : ℂ) : Prop := z.im = 0

def floor : Number → Number := withDomain realDomain fun z => (⌊z.re⌋ : ℂ)

def ceiling : Number → Number := withDomain realDomain fun z => (⌈z.re⌉ : ℂ)

end Nary
