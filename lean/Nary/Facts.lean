import Mathlib.Data.List.Perm.Basic
import Nary.Number

namespace Nary

def Unordered {α β : Type*} (f : List α → β) : Prop :=
  ∀ xs ys : List α, xs.Perm ys → f xs = f ys

def Flat {α : Type*} (f : List α → α) : Prop :=
  ∀ xs ys zs : List α, f (xs ++ f ys :: zs) = f (xs ++ ys ++ zs)

def Identity {α : Type*} (f : List α → α) (e : α) : Prop :=
  f [] = e ∧ (∀ a, f [a] = a) ∧ ∀ xs ys : List α, f (xs ++ e :: ys) = f (xs ++ ys)

def Absorbing {α : Type*} (f : List (Option α) → Option α) (z : Option α) : Prop :=
  ∀ xs ys : List (Option α), (∀ x ∈ xs ++ ys, x ≠ none) → f (xs ++ z :: ys) = z

def Idempotent {α : Type*} (f : List α → α) : Prop :=
  ∀ (xs ys zs : List α) (a : α), f (xs ++ a :: ys ++ a :: zs) = f (xs ++ a :: ys ++ zs)

def Involution {α : Type*} (f : α → α) : Prop :=
  ∀ a, f (f a) = a

def Repeats {α : Type*} (f : List (Option α) → Option α) (g : Option α → Number → Option α) :
    Prop :=
  (∀ a, g a (lit 1) = a) ∧ (∀ a, g a (lit 0) ≠ none → g a (lit 0) = f []) ∧
    ∀ a m n, (f [g a m, g a n] ≠ none ↔ g a (Add [m, n]) ≠ none) →
      f [g a m, g a n] = g a (Add [m, n])

end Nary
