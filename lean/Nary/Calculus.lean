import Mathlib.Analysis.Calculus.Deriv.Basic
import Nary.Number

noncomputable section
open Classical Filter Topology

namespace Nary

abbrev NumberFunction := ℂ → Number

def apply (f : NumberFunction) (a : Number) : Number := a.bind f

-- This is the complex derivative, so Derivative(re) has no value anywhere (not confirmed by the owner).
def Derivative (f : NumberFunction) : NumberFunction := fun a =>
  let g : ℂ → ℂ := fun z => (f z).getD 0
  if (∀ᶠ z in 𝓝 a, (f z).isSome) ∧ DifferentiableAt ℂ g a then some (deriv g a)
  else none

end Nary
