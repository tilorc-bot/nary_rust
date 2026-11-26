import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.LogicRules.Statement

abbrev and_identity : Prop :=
  ∀ (a : Nary.Boolean), Nary.And [a, Nary.true] = a

abbrev and_absorbing : Prop :=
  ∀ (a : Nary.Boolean), a ≠ none → Nary.And [a, Nary.false] = Nary.false

abbrev and_idempotent : Prop :=
  ∀ (a : Nary.Boolean), Nary.And [a, a] = a

abbrev and_empty : Prop :=
  Nary.And [] = Nary.true

abbrev and_single : Prop :=
  ∀ (p : Nary.Boolean), Nary.And [p] = p

abbrev and_contradiction : Prop :=
  ∀ (p : Nary.Boolean), p ≠ none → Nary.And [p, Nary.Not p] = Nary.false

abbrev and_absorption : Prop :=
  ∀ (p : Nary.Boolean) (ps : List Nary.Boolean), (∀ x ∈ ps, x ≠ none) → Nary.And [p, Nary.Or ([p] ++ ps)] = p

abbrev or_identity : Prop :=
  ∀ (a : Nary.Boolean), Nary.Or [a, Nary.false] = a

abbrev or_absorbing : Prop :=
  ∀ (a : Nary.Boolean), a ≠ none → Nary.Or [a, Nary.true] = Nary.true

abbrev or_idempotent : Prop :=
  ∀ (a : Nary.Boolean), Nary.Or [a, a] = a

abbrev or_empty : Prop :=
  Nary.Or [] = Nary.false

abbrev or_single : Prop :=
  ∀ (p : Nary.Boolean), Nary.Or [p] = p

abbrev or_excluded_middle : Prop :=
  ∀ (p : Nary.Boolean), p ≠ none → Nary.Or [p, Nary.Not p] = Nary.true

abbrev or_absorption : Prop :=
  ∀ (p : Nary.Boolean) (ps : List Nary.Boolean), (∀ x ∈ ps, x ≠ none) → Nary.Or [p, Nary.And ([p] ++ ps)] = p

abbrev not_not : Prop :=
  ∀ (p : Nary.Boolean), Nary.Not (Nary.Not p) = p

abbrev not_true : Prop :=
  Nary.Not Nary.true = Nary.false

abbrev not_false : Prop :=
  Nary.Not Nary.false = Nary.true

abbrev not_eq : Prop :=
  ∀ (a b : Nary.Number), Nary.Not (Nary.Eq a b) = Nary.Ne a b

abbrev not_ne : Prop :=
  ∀ (a b : Nary.Number), Nary.Not (Nary.Ne a b) = Nary.Eq a b

abbrev not_lt : Prop :=
  ∀ (a b : Nary.Number), Nary.Not (Nary.Lt a b) = Nary.Ge a b

abbrev not_le : Prop :=
  ∀ (a b : Nary.Number), Nary.Not (Nary.Le a b) = Nary.Gt a b

abbrev not_gt : Prop :=
  ∀ (a b : Nary.Number), Nary.Not (Nary.Gt a b) = Nary.Le a b

abbrev not_ge : Prop :=
  ∀ (a b : Nary.Number), Nary.Not (Nary.Ge a b) = Nary.Lt a b

abbrev not_and : Prop :=
  ∀ (p : Nary.Boolean) (ps : List Nary.Boolean), Nary.Not (Nary.And ([p] ++ ps)) = Nary.Or [Nary.Not p, Nary.Not (Nary.And ps)]

abbrev not_or : Prop :=
  ∀ (p : Nary.Boolean) (ps : List Nary.Boolean), Nary.Not (Nary.Or ([p] ++ ps)) = Nary.And [Nary.Not p, Nary.Not (Nary.Or ps)]

abbrev eq_self : Prop :=
  ∀ (a : Nary.Number), a ≠ none → Nary.Eq a a = Nary.true

abbrev ne_self : Prop :=
  ∀ (a : Nary.Number), a ≠ none → Nary.Ne a a = Nary.false

abbrev lt_self : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → a ≠ none → Nary.Lt a a = Nary.false

abbrev le_self : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → a ≠ none → Nary.Le a a = Nary.true

abbrev gt_self : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → a ≠ none → Nary.Gt a a = Nary.false

abbrev ge_self : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → a ≠ none → Nary.Ge a a = Nary.true

abbrev and_unordered : Prop :=
  Nary.Unordered Nary.And

abbrev and_flat : Prop :=
  Nary.Flat Nary.And

abbrev or_unordered : Prop :=
  Nary.Unordered Nary.Or

abbrev or_flat : Prop :=
  Nary.Flat Nary.Or

end Nary.LogicRules.Statement
