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

def Dominant {α : Type*} (f : List α → α) (z : α) : Prop :=
  ∀ xs ys : List α, f (xs ++ z :: ys) = z

def Idempotent {α : Type*} (f : List α → α) : Prop :=
  ∀ (xs ys zs : List α) (a : α), f (xs ++ a :: ys ++ a :: zs) = f (xs ++ a :: ys ++ zs)

def Involution {α : Type*} (f : α → α) : Prop :=
  ∀ a, f (f a) = a

def Repeats {α : Type*} (f : List (Option α) → Option α) (g : Option α → Number → Option α) :
    Prop :=
  (∀ a, g a (lit 1) = a) ∧ (∀ a, g a (lit 0) ≠ none → g a (lit 0) = f []) ∧
    ∀ a m n, (f [g a m, g a n] ≠ none ↔ g a (Add [m, n]) ≠ none) →
      f [g a m, g a n] = g a (Add [m, n])

def Maps (h : Number → Number) (F G : List Number → Number) (c : Number → Prop) : Prop :=
  h (F []) = G [] ∧ ∀ a as, c a → (h (F (a :: as)) ≠ none ↔ G [h a, h (F as)] ≠ none) →
    h (F (a :: as)) = G [h a, h (F as)]

def Maps₁ (h F G : Number → Number) : Prop :=
  ∀ a, (h (F a) ≠ none ↔ G (h a) ≠ none) → h (F a) = G (h a)

def Undoes (h k : Number → Number) (c : Number → Prop) : Prop :=
  ∀ a, c a → (h (k a) ≠ none ↔ a ≠ none) → h (k a) = a

def Composes (g : Number → Number → Number) (F : List Number → Number)
    (c : Number → Number → Prop) : Prop :=
  ∀ a m n, c (g a m) n → (g (g a m) n ≠ none ↔ g a (F [m, n]) ≠ none) →
    g (g a m) n = g a (F [m, n])

end Nary
