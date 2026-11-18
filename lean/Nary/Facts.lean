/-
What the two facts that `python/nary/rules.py` records about a function mean:
`unordered(f)` and `flat(f)`. They are defined here for a function that takes
its arguments as a list, which is how `Add`, `Mul`, `And` and `Or` are
defined. The rewriting engine (`python/nary/rewriting.py`) relies on them
when it matches some of the arguments of a longer `Add` or `Mul`.
-/
import Mathlib.Data.List.Perm.Basic

namespace Nary

/-- `unordered(f)`: the order of the arguments does not change the value.
Two lists are permutations of each other (`List.Perm`) when they have the
same elements, each the same number of times. -/
def Unordered {α β : Type*} (f : List α → β) : Prop :=
  ∀ xs ys : List α, xs.Perm ys → f xs = f ys

/-- `flat(f)`: an application of `f` directly among the arguments of `f`, at
any position, can be merged into it: `f [a, f [b, c], d] = f [a, b, c, d]`. -/
def Flat {α : Type*} (f : List α → α) : Prop :=
  ∀ xs ys zs : List α, f (xs ++ f ys :: zs) = f (xs ++ ys ++ zs)

end Nary
