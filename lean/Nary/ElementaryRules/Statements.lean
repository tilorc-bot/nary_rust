import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.ElementaryRules.Statement

abbrev sin_odd : Prop :=
  ∀ (c : Nary.Number) (rest : List Nary.Number), Nary.Holds (Nary.Lt c (Nary.lit 0)) → Nary.sin (Nary.Mul ([c] ++ rest)) = Nary.Mul [Nary.lit (-1), Nary.sin (Nary.Mul ([Nary.Mul [Nary.lit (-1), c]] ++ rest))]

abbrev sin_shift_down : Prop :=
  ∀ (cs rest : List Nary.Number), Nary.Holds (Nary.Ge (Nary.Mul cs) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))) → Nary.sin (Nary.Add ([Nary.Mul ([Nary.pi] ++ cs)] ++ rest)) = Nary.cos (Nary.Add ([Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 2) (Nary.lit (-1))]], Nary.pi]] ++ rest))

abbrev sin_shift_up : Prop :=
  ∀ (cs rest : List Nary.Number), Nary.Holds (Nary.Lt (Nary.Mul cs) (Nary.lit 0)) → Nary.sin (Nary.Add ([Nary.Mul ([Nary.pi] ++ cs)] ++ rest)) = Nary.Mul [Nary.lit (-1), Nary.cos (Nary.Add ([Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Pow (Nary.lit 2) (Nary.lit (-1))], Nary.pi]] ++ rest))]

abbrev sin_zero : Prop :=
  Nary.sin (Nary.lit 0) = Nary.lit 0

abbrev sin_pi_6 : Prop :=
  Nary.sin (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 6) (Nary.lit (-1))]) = Nary.Pow (Nary.lit 2) (Nary.lit (-1))

abbrev sin_pi_4 : Prop :=
  Nary.sin (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 4) (Nary.lit (-1))]) = Nary.Mul [Nary.Pow (Nary.lit 2) (Nary.lit (-1)), Nary.Pow (Nary.lit 2) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]

abbrev sin_pi_3 : Prop :=
  Nary.sin (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 3) (Nary.lit (-1))]) = Nary.Mul [Nary.Pow (Nary.lit 2) (Nary.lit (-1)), Nary.Pow (Nary.lit 3) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]

abbrev cos_even : Prop :=
  ∀ (c : Nary.Number) (rest : List Nary.Number), Nary.Holds (Nary.Lt c (Nary.lit 0)) → Nary.cos (Nary.Mul ([c] ++ rest)) = Nary.cos (Nary.Mul ([Nary.Mul [Nary.lit (-1), c]] ++ rest))

abbrev cos_shift_down : Prop :=
  ∀ (cs rest : List Nary.Number), Nary.Holds (Nary.Ge (Nary.Mul cs) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))) → Nary.cos (Nary.Add ([Nary.Mul ([Nary.pi] ++ cs)] ++ rest)) = Nary.Mul [Nary.lit (-1), Nary.sin (Nary.Add ([Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 2) (Nary.lit (-1))]], Nary.pi]] ++ rest))]

abbrev cos_shift_up : Prop :=
  ∀ (cs rest : List Nary.Number), Nary.Holds (Nary.Lt (Nary.Mul cs) (Nary.lit 0)) → Nary.cos (Nary.Add ([Nary.Mul ([Nary.pi] ++ cs)] ++ rest)) = Nary.sin (Nary.Add ([Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Pow (Nary.lit 2) (Nary.lit (-1))], Nary.pi]] ++ rest))

abbrev cos_zero : Prop :=
  Nary.cos (Nary.lit 0) = Nary.lit 1

abbrev cos_pi_6 : Prop :=
  Nary.cos (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 6) (Nary.lit (-1))]) = Nary.Mul [Nary.Pow (Nary.lit 2) (Nary.lit (-1)), Nary.Pow (Nary.lit 3) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]

abbrev cos_pi_4 : Prop :=
  Nary.cos (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 4) (Nary.lit (-1))]) = Nary.Mul [Nary.Pow (Nary.lit 2) (Nary.lit (-1)), Nary.Pow (Nary.lit 2) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]

abbrev cos_pi_3 : Prop :=
  Nary.cos (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 3) (Nary.lit (-1))]) = Nary.Pow (Nary.lit 2) (Nary.lit (-1))

abbrev pythagoras : Prop :=
  ∀ (a : Nary.Number), a ≠ none → Nary.Add [Nary.Pow (Nary.sin a) (Nary.lit 2), Nary.Pow (Nary.cos a) (Nary.lit 2)] = Nary.lit 1

abbrev pythagoras_scaled : Prop :=
  ∀ (b a : Nary.Number), a ≠ none → Nary.Add [Nary.Mul [b, Nary.Pow (Nary.sin a) (Nary.lit 2)], Nary.Mul [b, Nary.Pow (Nary.cos a) (Nary.lit 2)]] = b

abbrev one_minus_sin_squared : Prop :=
  ∀ (a : Nary.Number), Nary.Add [Nary.lit 1, Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.sin a) (Nary.lit 2)]] = Nary.Pow (Nary.cos a) (Nary.lit 2)

abbrev one_minus_cos_squared : Prop :=
  ∀ (a : Nary.Number), Nary.Add [Nary.lit 1, Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.cos a) (Nary.lit 2)]] = Nary.Pow (Nary.sin a) (Nary.lit 2)

abbrev tan_odd : Prop :=
  ∀ (c : Nary.Number) (rest : List Nary.Number), Nary.Holds (Nary.Lt c (Nary.lit 0)) → Nary.tan (Nary.Mul ([c] ++ rest)) = Nary.Mul [Nary.lit (-1), Nary.tan (Nary.Mul ([Nary.Mul [Nary.lit (-1), c]] ++ rest))]

abbrev tan_period_down : Prop :=
  ∀ (cs rest : List Nary.Number), Nary.Holds (Nary.Ge (Nary.Mul cs) (Nary.lit 1)) → Nary.tan (Nary.Add ([Nary.Mul ([Nary.pi] ++ cs)] ++ rest)) = Nary.tan (Nary.Add ([Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.lit 1]], Nary.pi]] ++ rest))

abbrev tan_period_up : Prop :=
  ∀ (cs rest : List Nary.Number), Nary.Holds (Nary.Lt (Nary.Mul cs) (Nary.lit 0)) → Nary.tan (Nary.Add ([Nary.Mul ([Nary.pi] ++ cs)] ++ rest)) = Nary.tan (Nary.Add ([Nary.Mul [Nary.Add [Nary.Mul cs, Nary.lit 1], Nary.pi]] ++ rest))

abbrev tan_zero : Prop :=
  Nary.tan (Nary.lit 0) = Nary.lit 0

abbrev tan_pi_4 : Prop :=
  Nary.tan (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 4) (Nary.lit (-1))]) = Nary.lit 1

abbrev sin_over_cos : Prop :=
  ∀ (a : Nary.Number), Nary.Mul [Nary.sin a, Nary.Pow (Nary.cos a) (Nary.lit (-1))] = Nary.tan a

abbrev re_real : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → Nary.re a = a

abbrev re_pi : Prop :=
  Nary.re Nary.pi = Nary.pi

abbrev re_e : Prop :=
  Nary.re Nary.E = Nary.E

abbrev re_i : Prop :=
  Nary.re Nary.I = Nary.lit 0

abbrev re_re : Prop :=
  ∀ (a : Nary.Number), Nary.re (Nary.re a) = Nary.re a

abbrev re_add : Prop :=
  ∀ (a : Nary.Number) (rest : List Nary.Number), Nary.re (Nary.Add ([a] ++ rest)) = Nary.Add [Nary.re a, Nary.re (Nary.Add rest)]

abbrev derivative_sin : Prop :=
  Nary.Derivative (fun z => Nary.sin (some z)) = fun z => Nary.cos (some z)

abbrev derivative_exp : Prop :=
  Nary.Derivative (fun z => Nary.exp (some z)) = fun z => Nary.exp (some z)

end Nary.ElementaryRules.Statement
