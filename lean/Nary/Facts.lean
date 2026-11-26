import Mathlib.Data.List.Perm.Basic

namespace Nary

def Unordered {α β : Type*} (f : List α → β) : Prop :=
  ∀ xs ys : List α, xs.Perm ys → f xs = f ys

def Flat {α : Type*} (f : List α → α) : Prop :=
  ∀ xs ys zs : List α, f (xs ++ f ys :: zs) = f (xs ++ ys ++ zs)

end Nary
