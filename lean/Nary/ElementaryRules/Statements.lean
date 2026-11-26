import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.ElementaryRules.Statement

abbrev sin_number_minus_term : Prop :=
  ∀ (n c d : Nary.Number) (rest : List Nary.Number), Nary.Holds (Nary.And [Nary.Gt (Nary.exp n) (Nary.lit 1), Nary.Lt (Nary.exp c) (Nary.lit 1)]) → Nary.sin (Nary.Add [n, Nary.Mul ([c, d] ++ rest)]) = Nary.Mul [Nary.lit (-1), Nary.sin (Nary.Mul [Nary.lit (-1), Nary.Add [n, Nary.Mul ([c, d] ++ rest)]])]

abbrev cos_number_minus_term : Prop :=
  ∀ (n c d : Nary.Number) (rest : List Nary.Number), Nary.Holds (Nary.And [Nary.Gt (Nary.exp n) (Nary.lit 1), Nary.Lt (Nary.exp c) (Nary.lit 1)]) → Nary.cos (Nary.Add [n, Nary.Mul ([c, d] ++ rest)]) = Nary.cos (Nary.Mul [Nary.lit (-1), Nary.Add [n, Nary.Mul ([c, d] ++ rest)]])

abbrev tan_number_minus_term : Prop :=
  ∀ (n c d : Nary.Number) (rest : List Nary.Number), Nary.Holds (Nary.And [Nary.Gt (Nary.exp n) (Nary.lit 1), Nary.Lt (Nary.exp c) (Nary.lit 1)]) → Nary.tan (Nary.Add [n, Nary.Mul ([c, d] ++ rest)]) = Nary.Mul [Nary.lit (-1), Nary.tan (Nary.Mul [Nary.lit (-1), Nary.Add [n, Nary.Mul ([c, d] ++ rest)]])]

abbrev re_real : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → Nary.re a = a

abbrev re_re : Prop :=
  ∀ (a : Nary.Number), Nary.re (Nary.re a) = Nary.re a

abbrev re_real_factor : Prop :=
  ∀ (a b : Nary.Number) (rest : List Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → Nary.re (Nary.Mul ([a, b] ++ rest)) = Nary.Mul [a, Nary.re (Nary.Mul ([b] ++ rest))]

abbrev re_exp_real : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → Nary.re (Nary.exp a) = Nary.exp a

abbrev log_negative_number : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.And [Nary.Lt a (Nary.lit 0), Nary.Lt (Nary.exp a) (Nary.lit 1)]) → Nary.log a = Nary.Add [Nary.log (Nary.Mul [Nary.lit (-1), a]), Nary.Mul [Nary.I, Nary.pi]]

abbrev derivative_sin : Prop :=
  Nary.Derivative (fun z => Nary.sin (some z)) = fun z => Nary.cos (some z)

abbrev derivative_exp : Prop :=
  Nary.Derivative (fun z => Nary.exp (some z)) = fun z => Nary.exp (some z)

end Nary.ElementaryRules.Statement
