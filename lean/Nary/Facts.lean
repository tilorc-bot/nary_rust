/-
What the generic identities of `python/nary/identities.py` mean, one
definition each, for a function that takes its arguments as a list, which is
how `Add`, `Mul`, `And` and `Or` are defined. An identity listed for a
function is stated as its definition applied to that function and the
parameters, as in `Nary.Identity Nary.Add (Nary.lit 0)`.

`Unordered` is commutative and `Flat` is associative; they are also what the
facts `unordered(f)` and `flat(f)` of `python/nary/rules.py` mean. The
rewriting engine (`python/nary/rewriting.py`) relies on them when it matches
some of the arguments of a longer `Add` or `Mul`.

As for a rule, an identity is claimed where the holes it erases (in its left
side and not its right) have a value; only `Absorbing` erases any.
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

/-- `singleton`: `f(a) = a`. -/
def Singleton {α : Type*} (f : List α → α) : Prop :=
  ∀ a : α, f [a] = a

/-- `identity(e)`: `f(s, e, t) = f(s, t)`, an argument `e` can be dropped. -/
def Identity {α : Type*} (f : List α → α) (e : α) : Prop :=
  ∀ xs ys : List α, f (xs ++ e :: ys) = f (xs ++ ys)

/-- `idempotent`: `f(s, a, t, a, u) = f(s, a, t, u)`, a repeated argument can
be dropped. -/
def Idempotent {α : Type*} (f : List α → α) : Prop :=
  ∀ (xs ys zs : List α) (a : α), f (xs ++ a :: ys ++ a :: zs) = f (xs ++ a :: ys ++ zs)

/-- `absorbing(z)`: `f(s, z, t) = z` where the arguments `s` and `t`, which
the right side erases, have a value. -/
def Absorbing {β : Type*} (f : List (Option β) → Option β) (z : Option β) : Prop :=
  ∀ xs ys : List (Option β), (∀ x ∈ xs ++ ys, x ≠ none) → f (xs ++ z :: ys) = z

/-- `distributive(g)`: `f(a, g(b, c)) = g(f(a, b), f(a, c))`. -/
def Distributive {α : Type*} (f g : List α → α) : Prop :=
  ∀ a b c : α, f [a, g [b, c]] = g [f [a, b], f [a, c]]

/-! The rules that `nary.rules.identity_rules` gives the engine for these
identities follow from them. -/

theorem Identity.rule {α : Type*} {f : List α → α} {e : α}
    (h : Identity f e) (hs : Singleton f) (a : α) : f [a, e] = a :=
  (h [a] []).trans (hs a)

theorem Idempotent.rule {α : Type*} {f : List α → α}
    (h : Idempotent f) (hs : Singleton f) (a : α) : f [a, a] = a :=
  (h [] [] [] a).trans (hs a)

theorem Absorbing.rule {β : Type*} {f : List (Option β) → Option β} {z : Option β}
    (h : Absorbing f z) (a : Option β) (ha : a ≠ none) : f [a, z] = z :=
  h [a] [] (by simpa using ha)

end Nary
