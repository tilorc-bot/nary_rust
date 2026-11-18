/-
What a function of one number means, and the calculus functions of
`calculus.py` that can be given a meaning now.

An expression of kind `FunctionKind((NumberKind,), NumberKind)` means a
function from complex numbers to "a complex number or no value",
`ℂ → Option ℂ`. A declared function is one of these: `sin` means
`fun z => sin (some z)`. A lambda `Lambda(x, body)` means `fun x => body`,
with `x` read as `some x` inside the body.

`Integral`, `Sum`, `Product`, `Limit` and `Antiderivative` are left out:
their Python declarations do not say enough to fix a meaning. `lean/README.md`
lists the question each one leaves open.
-/
import Mathlib.Analysis.Calculus.Deriv.Basic
import Nary.Number

noncomputable section
open Classical Filter Topology

namespace Nary

/-- What a `FunctionKind((NumberKind,), NumberKind)` expression means. -/
abbrev NumberFunction := ℂ → Number

/-- Applying a function to an argument, `f(a)`. It has no value when `a` has
none, and otherwise it is `f` at the value of `a`. -/
def apply (f : NumberFunction) (a : Number) : Number := a.bind f

/-- `Derivative(f)`, the complex derivative of `f`. `Derivative(f)(a)` has a
value when `f` has a value at every point near `a` (on some open disc around
`a`) and is complex-differentiable at `a`; the value is then the derivative.

Not confirmed by the owner: this is the complex derivative, so for example
`Derivative(re)` has no value anywhere, although `re` has a derivative along
the real line.

`(f z).getD 0` is the value of `f` at `z`, or 0 where `f` has none. The 0 is
never seen: the condition makes `f` have a value near `a`, and the derivative
at `a` depends only on the values near `a`. -/
def Derivative (f : NumberFunction) : NumberFunction := fun a =>
  let g : ℂ → ℂ := fun z => (f z).getD 0
  if (∀ᶠ z in 𝓝 a, (f z).isSome) ∧ DifferentiableAt ℂ g a then some (deriv g a)
  else none

end Nary
