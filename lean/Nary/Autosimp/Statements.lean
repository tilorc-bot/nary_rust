import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.Autosimp.Statement

abbrev pow_one : Prop :=
  ∀ (a : Nary.Number), Nary.Pow a (Nary.lit 1) = a

abbrev pow_zero : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Ne a (Nary.lit 0)) → a ≠ none → Nary.Pow a (Nary.lit 0) = Nary.lit 1

abbrev one_pow : Prop :=
  ∀ (a : Nary.Number), a ≠ none → Nary.Pow (Nary.lit 1) a = Nary.lit 1

abbrev zero_pow : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Gt (Nary.re a) (Nary.lit 0)) → a ≠ none → Nary.Pow (Nary.lit 0) a = Nary.lit 0

abbrev e_pow : Prop :=
  ∀ (a : Nary.Number), Nary.Pow Nary.E a = Nary.exp a

abbrev exp_zero : Prop :=
  Nary.exp (Nary.lit 0) = Nary.lit 1

abbrev exp_one : Prop :=
  Nary.exp (Nary.lit 1) = Nary.E

abbrev exp_log : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Ne a (Nary.lit 0)) → Nary.exp (Nary.log a) = a

abbrev log_one : Prop :=
  Nary.log (Nary.lit 1) = Nary.lit 0

abbrev log_e : Prop :=
  Nary.log Nary.E = Nary.lit 1

abbrev log_exp : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → Nary.log (Nary.exp a) = a

abbrev re_real : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → Nary.re a = a

abbrev re_i : Prop :=
  Nary.re Nary.I = Nary.lit 0

abbrev not_true : Prop :=
  Nary.Not Nary.true = Nary.false

abbrev not_false : Prop :=
  Nary.Not Nary.false = Nary.true

abbrev not_not : Prop :=
  ∀ (p : Nary.Boolean), Nary.Not (Nary.Not p) = p

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

end Nary.Autosimp.Statement
