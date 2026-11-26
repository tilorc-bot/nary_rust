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

abbrev pow_e : Prop :=
  ∀ (a : Nary.Number), Nary.Pow Nary.E a = Nary.exp a

abbrev pow_complex : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.And [Nary.Ne a (Nary.lit 0), Nary.Ne (Nary.re b) b]) → Nary.Pow a b = Nary.exp (Nary.Mul [b, Nary.log a])

abbrev e_pow : Prop :=
  ∀ (a : Nary.Number), Nary.Pow Nary.E a = Nary.exp a

abbrev exp_zero : Prop :=
  Nary.exp (Nary.lit 0) = Nary.lit 1

abbrev exp_one : Prop :=
  Nary.exp (Nary.lit 1) = Nary.E

abbrev exp_log : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Ne a (Nary.lit 0)) → Nary.exp (Nary.log a) = a

abbrev exp_log_power : Prop :=
  ∀ (a : Nary.Number) (cs : List Nary.Number), Nary.Holds (Nary.And [Nary.Ne a (Nary.lit 0), Nary.Eq (Nary.re (Nary.Mul cs)) (Nary.Mul cs)]) → Nary.exp (Nary.Mul ([Nary.log a] ++ cs)) = Nary.Pow a (Nary.Mul cs)

abbrev exp_pow : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → Nary.Pow (Nary.exp a) b = Nary.exp (Nary.Mul [a, b])

abbrev exp_period_down : Prop :=
  ∀ (cs rest : List Nary.Number), Nary.Holds (Nary.Gt (Nary.Mul cs) (Nary.lit 1)) → Nary.exp (Nary.Add ([Nary.Mul ([Nary.I, Nary.pi] ++ cs)] ++ rest)) = Nary.exp (Nary.Add ([Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.lit 2]], Nary.I, Nary.pi]] ++ rest))

abbrev exp_period_up : Prop :=
  ∀ (cs rest : List Nary.Number), Nary.Holds (Nary.Le (Nary.Mul cs) (Nary.lit (-1))) → Nary.exp (Nary.Add ([Nary.Mul ([Nary.I, Nary.pi] ++ cs)] ++ rest)) = Nary.exp (Nary.Add ([Nary.Mul [Nary.Add [Nary.Mul cs, Nary.lit 2], Nary.I, Nary.pi]] ++ rest))

abbrev exp_i_pi : Prop :=
  ∀ (rest : List Nary.Number), Nary.exp (Nary.Add ([Nary.Mul [Nary.I, Nary.pi]] ++ rest)) = Nary.Mul [Nary.lit (-1), Nary.exp (Nary.Add rest)]

abbrev exp_half_i_pi : Prop :=
  ∀ (rest : List Nary.Number), Nary.exp (Nary.Add ([Nary.Mul [Nary.Pow (Nary.lit 2) (Nary.lit (-1)), Nary.I, Nary.pi]] ++ rest)) = Nary.Mul [Nary.I, Nary.exp (Nary.Add rest)]

abbrev exp_minus_half_i_pi : Prop :=
  ∀ (rest : List Nary.Number), Nary.exp (Nary.Add ([Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 2) (Nary.lit (-1)), Nary.I, Nary.pi]] ++ rest)) = Nary.Mul [Nary.Mul [Nary.lit (-1), Nary.I], Nary.exp (Nary.Add rest)]

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
