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

abbrev eq_self : Prop :=
  ∀ (a : Nary.Number), a ≠ none → Nary.Eq a a = Nary.true

abbrev eq_holds : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Eq a b) → a ≠ none → b ≠ none → Nary.Eq a b = Nary.true

abbrev eq_fails : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Ne a b) → a ≠ none → b ≠ none → Nary.Eq a b = Nary.false

abbrev ne_self : Prop :=
  ∀ (a : Nary.Number), a ≠ none → Nary.Ne a a = Nary.false

abbrev ne_holds : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Ne a b) → a ≠ none → b ≠ none → Nary.Ne a b = Nary.true

abbrev ne_fails : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Eq a b) → a ≠ none → b ≠ none → Nary.Ne a b = Nary.false

abbrev lt_self : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → a ≠ none → Nary.Lt a a = Nary.false

abbrev lt_holds : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Lt a b) → a ≠ none → b ≠ none → Nary.Lt a b = Nary.true

abbrev lt_fails : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Ge a b) → a ≠ none → b ≠ none → Nary.Lt a b = Nary.false

abbrev le_self : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → a ≠ none → Nary.Le a a = Nary.true

abbrev le_holds : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Le a b) → a ≠ none → b ≠ none → Nary.Le a b = Nary.true

abbrev le_fails : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Gt a b) → a ≠ none → b ≠ none → Nary.Le a b = Nary.false

abbrev gt_self : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → a ≠ none → Nary.Gt a a = Nary.false

abbrev gt_holds : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Gt a b) → a ≠ none → b ≠ none → Nary.Gt a b = Nary.true

abbrev gt_fails : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Le a b) → a ≠ none → b ≠ none → Nary.Gt a b = Nary.false

abbrev ge_self : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → a ≠ none → Nary.Ge a a = Nary.true

abbrev ge_holds : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Ge a b) → a ≠ none → b ≠ none → Nary.Ge a b = Nary.true

abbrev ge_fails : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Lt a b) → a ≠ none → b ≠ none → Nary.Ge a b = Nary.false

abbrev and_unordered : Prop :=
  Nary.Unordered Nary.And

abbrev and_flat : Prop :=
  Nary.Flat Nary.And

abbrev or_unordered : Prop :=
  Nary.Unordered Nary.Or

abbrev or_flat : Prop :=
  Nary.Flat Nary.Or

end Nary.LogicRules.Statement
