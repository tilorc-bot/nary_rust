import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.ElementaryRules.Statement

abbrev sin_minus_pi : Prop :=
  ∀ (cs : List Nary.Number), Nary.Holds (Nary.Gt (Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.lit 1]]) (Nary.lit 0)) → Nary.sin (Nary.Mul ([Nary.pi] ++ cs)) = Nary.Mul [Nary.lit (-1), Nary.sin (Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.lit 1]], Nary.pi])]

abbrev sin_reflect : Prop :=
  ∀ (cs : List Nary.Number), Nary.Holds (Nary.And [Nary.Gt (Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 2) (Nary.lit (-1))]]) (Nary.lit 0), Nary.Le (Nary.Mul cs) (Nary.lit 1)]) → Nary.sin (Nary.Mul ([Nary.pi] ++ cs)) = Nary.sin (Nary.Mul [Nary.Add [Nary.lit 1, Nary.Mul [Nary.lit (-1), Nary.Mul cs]], Nary.pi])

abbrev sin_shift_down : Prop :=
  ∀ (b : Nary.Number) (cs rest : List Nary.Number), Nary.Holds (Nary.Ge (Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 2) (Nary.lit (-1))]]) (Nary.lit 0)) → Nary.sin (Nary.Add ([Nary.Mul ([Nary.pi] ++ cs), b] ++ rest)) = Nary.cos (Nary.Add ([Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 2) (Nary.lit (-1))]], Nary.pi], b] ++ rest))

abbrev sin_shift_up : Prop :=
  ∀ (b : Nary.Number) (cs rest : List Nary.Number), Nary.Holds (Nary.Lt (Nary.Mul cs) (Nary.lit 0)) → Nary.sin (Nary.Add ([Nary.Mul ([Nary.pi] ++ cs), b] ++ rest)) = Nary.Mul [Nary.lit (-1), Nary.cos (Nary.Add ([Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Pow (Nary.lit 2) (Nary.lit (-1))], Nary.pi], b] ++ rest))]

abbrev sin_odd : Prop :=
  ∀ (c : Nary.Number) (rest : List Nary.Number), Nary.Holds (Nary.Lt (Nary.exp c) (Nary.lit 1)) → Nary.sin (Nary.Mul ([c] ++ rest)) = Nary.Mul [Nary.lit (-1), Nary.sin (Nary.Mul [Nary.lit (-1), Nary.Mul ([c] ++ rest)])]

abbrev sin_odd_two_negative_terms : Prop :=
  ∀ (c d : Nary.Number) (r1 r2 : List Nary.Number), Nary.Holds (Nary.And [Nary.Lt (Nary.exp c) (Nary.lit 1), Nary.Lt (Nary.exp d) (Nary.lit 1)]) → Nary.sin (Nary.Add [Nary.Mul ([c] ++ r1), Nary.Mul ([d] ++ r2)]) = Nary.Mul [Nary.lit (-1), Nary.sin (Nary.Mul [Nary.lit (-1), Nary.Add [Nary.Mul ([c] ++ r1), Nary.Mul ([d] ++ r2)]])]

abbrev sin_odd_two_of_three_negative : Prop :=
  ∀ (c d b : Nary.Number) (r1 r2 : List Nary.Number), Nary.Holds (Nary.And [Nary.Lt (Nary.exp c) (Nary.lit 1), Nary.Lt (Nary.exp d) (Nary.lit 1)]) → Nary.sin (Nary.Add [Nary.Mul ([c] ++ r1), Nary.Mul ([d] ++ r2), b]) = Nary.Mul [Nary.lit (-1), Nary.sin (Nary.Mul [Nary.lit (-1), Nary.Add [Nary.Mul ([c] ++ r1), Nary.Mul ([d] ++ r2), b]])]

abbrev sin_odd_number_minus_term : Prop :=
  ∀ (n c d : Nary.Number) (r1 : List Nary.Number), Nary.Holds (Nary.And [Nary.Gt (Nary.exp n) (Nary.lit 1), Nary.Lt (Nary.exp c) (Nary.lit 1)]) → Nary.sin (Nary.Add [n, Nary.Mul ([c, d] ++ r1)]) = Nary.Mul [Nary.lit (-1), Nary.sin (Nary.Mul [Nary.lit (-1), Nary.Add [n, Nary.Mul ([c, d] ++ r1)]])]

abbrev sin_zero : Prop :=
  Nary.sin (Nary.lit 0) = Nary.lit 0

abbrev sin_pi_2 : Prop :=
  Nary.sin (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 2) (Nary.lit (-1))]) = Nary.lit 1

abbrev sin_5pi_12 : Prop :=
  Nary.sin (Nary.Mul [Nary.lit 5, Nary.pi, Nary.Pow (Nary.lit 12) (Nary.lit (-1))]) = Nary.Mul [Nary.Add [Nary.Pow (Nary.lit 2) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 6) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))], Nary.Pow (Nary.lit 4) (Nary.lit (-1))]

abbrev sin_2pi_5 : Prop :=
  Nary.sin (Nary.Mul [Nary.lit 2, Nary.pi, Nary.Pow (Nary.lit 5) (Nary.lit (-1))]) = Nary.Pow (Nary.Add [Nary.Mul [Nary.lit 5, Nary.Pow (Nary.lit 8) (Nary.lit (-1))], Nary.Mul [Nary.Pow (Nary.lit 5) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 8) (Nary.lit (-1))]]) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))

abbrev sin_3pi_8 : Prop :=
  Nary.sin (Nary.Mul [Nary.lit 3, Nary.pi, Nary.Pow (Nary.lit 8) (Nary.lit (-1))]) = Nary.Pow (Nary.Add [Nary.Pow (Nary.lit 2) (Nary.lit (-1)), Nary.Mul [Nary.Pow (Nary.lit 2) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 4) (Nary.lit (-1))]]) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))

abbrev sin_pi_3 : Prop :=
  Nary.sin (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 3) (Nary.lit (-1))]) = Nary.Mul [Nary.Pow (Nary.lit 2) (Nary.lit (-1)), Nary.Pow (Nary.lit 3) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]

abbrev sin_3pi_10 : Prop :=
  Nary.sin (Nary.Mul [Nary.lit 3, Nary.pi, Nary.Pow (Nary.lit 10) (Nary.lit (-1))]) = Nary.Add [Nary.Pow (Nary.lit 4) (Nary.lit (-1)), Nary.Mul [Nary.Pow (Nary.lit 5) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 4) (Nary.lit (-1))]]

abbrev sin_pi_4 : Prop :=
  Nary.sin (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 4) (Nary.lit (-1))]) = Nary.Mul [Nary.Pow (Nary.lit 2) (Nary.lit (-1)), Nary.Pow (Nary.lit 2) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]

abbrev sin_pi_5 : Prop :=
  Nary.sin (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 5) (Nary.lit (-1))]) = Nary.Pow (Nary.Add [Nary.Mul [Nary.lit 5, Nary.Pow (Nary.lit 8) (Nary.lit (-1))], Nary.Mul [Nary.lit (-1), Nary.Mul [Nary.Pow (Nary.lit 5) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 8) (Nary.lit (-1))]]]) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))

abbrev sin_pi_6 : Prop :=
  Nary.sin (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 6) (Nary.lit (-1))]) = Nary.Pow (Nary.lit 2) (Nary.lit (-1))

abbrev sin_pi_8 : Prop :=
  Nary.sin (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 8) (Nary.lit (-1))]) = Nary.Pow (Nary.Add [Nary.Pow (Nary.lit 2) (Nary.lit (-1)), Nary.Mul [Nary.lit (-1), Nary.Mul [Nary.Pow (Nary.lit 2) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 4) (Nary.lit (-1))]]]) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))

abbrev sin_pi_10 : Prop :=
  Nary.sin (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 10) (Nary.lit (-1))]) = Nary.Add [Nary.Mul [Nary.Pow (Nary.lit 5) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 4) (Nary.lit (-1))], Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 4) (Nary.lit (-1))]]

abbrev sin_pi_12 : Prop :=
  Nary.sin (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 12) (Nary.lit (-1))]) = Nary.Mul [Nary.Add [Nary.Pow (Nary.lit 6) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 2) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]], Nary.Pow (Nary.lit 4) (Nary.lit (-1))]

abbrev cos_minus_pi : Prop :=
  ∀ (cs : List Nary.Number), Nary.Holds (Nary.Gt (Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.lit 1]]) (Nary.lit 0)) → Nary.cos (Nary.Mul ([Nary.pi] ++ cs)) = Nary.Mul [Nary.lit (-1), Nary.cos (Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.lit 1]], Nary.pi])]

abbrev cos_reflect : Prop :=
  ∀ (cs : List Nary.Number), Nary.Holds (Nary.And [Nary.Gt (Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 2) (Nary.lit (-1))]]) (Nary.lit 0), Nary.Le (Nary.Mul cs) (Nary.lit 1)]) → Nary.cos (Nary.Mul ([Nary.pi] ++ cs)) = Nary.Mul [Nary.lit (-1), Nary.cos (Nary.Mul [Nary.Add [Nary.lit 1, Nary.Mul [Nary.lit (-1), Nary.Mul cs]], Nary.pi])]

abbrev cos_shift_down : Prop :=
  ∀ (b : Nary.Number) (cs rest : List Nary.Number), Nary.Holds (Nary.Ge (Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 2) (Nary.lit (-1))]]) (Nary.lit 0)) → Nary.cos (Nary.Add ([Nary.Mul ([Nary.pi] ++ cs), b] ++ rest)) = Nary.Mul [Nary.lit (-1), Nary.sin (Nary.Add ([Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 2) (Nary.lit (-1))]], Nary.pi], b] ++ rest))]

abbrev cos_shift_up : Prop :=
  ∀ (b : Nary.Number) (cs rest : List Nary.Number), Nary.Holds (Nary.Lt (Nary.Mul cs) (Nary.lit 0)) → Nary.cos (Nary.Add ([Nary.Mul ([Nary.pi] ++ cs), b] ++ rest)) = Nary.sin (Nary.Add ([Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Pow (Nary.lit 2) (Nary.lit (-1))], Nary.pi], b] ++ rest))

abbrev cos_even : Prop :=
  ∀ (c : Nary.Number) (rest : List Nary.Number), Nary.Holds (Nary.Lt (Nary.exp c) (Nary.lit 1)) → Nary.cos (Nary.Mul ([c] ++ rest)) = Nary.cos (Nary.Mul [Nary.lit (-1), Nary.Mul ([c] ++ rest)])

abbrev cos_even_two_negative_terms : Prop :=
  ∀ (c d : Nary.Number) (r1 r2 : List Nary.Number), Nary.Holds (Nary.And [Nary.Lt (Nary.exp c) (Nary.lit 1), Nary.Lt (Nary.exp d) (Nary.lit 1)]) → Nary.cos (Nary.Add [Nary.Mul ([c] ++ r1), Nary.Mul ([d] ++ r2)]) = Nary.cos (Nary.Mul [Nary.lit (-1), Nary.Add [Nary.Mul ([c] ++ r1), Nary.Mul ([d] ++ r2)]])

abbrev cos_even_two_of_three_negative : Prop :=
  ∀ (c d b : Nary.Number) (r1 r2 : List Nary.Number), Nary.Holds (Nary.And [Nary.Lt (Nary.exp c) (Nary.lit 1), Nary.Lt (Nary.exp d) (Nary.lit 1)]) → Nary.cos (Nary.Add [Nary.Mul ([c] ++ r1), Nary.Mul ([d] ++ r2), b]) = Nary.cos (Nary.Mul [Nary.lit (-1), Nary.Add [Nary.Mul ([c] ++ r1), Nary.Mul ([d] ++ r2), b]])

abbrev cos_even_number_minus_term : Prop :=
  ∀ (n c d : Nary.Number) (r1 : List Nary.Number), Nary.Holds (Nary.And [Nary.Gt (Nary.exp n) (Nary.lit 1), Nary.Lt (Nary.exp c) (Nary.lit 1)]) → Nary.cos (Nary.Add [n, Nary.Mul ([c, d] ++ r1)]) = Nary.cos (Nary.Mul [Nary.lit (-1), Nary.Add [n, Nary.Mul ([c, d] ++ r1)]])

abbrev cos_zero : Prop :=
  Nary.cos (Nary.lit 0) = Nary.lit 1

abbrev cos_pi_12 : Prop :=
  Nary.cos (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 12) (Nary.lit (-1))]) = Nary.Mul [Nary.Add [Nary.Pow (Nary.lit 2) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 6) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))], Nary.Pow (Nary.lit 4) (Nary.lit (-1))]

abbrev cos_pi_10 : Prop :=
  Nary.cos (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 10) (Nary.lit (-1))]) = Nary.Pow (Nary.Add [Nary.Mul [Nary.lit 5, Nary.Pow (Nary.lit 8) (Nary.lit (-1))], Nary.Mul [Nary.Pow (Nary.lit 5) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 8) (Nary.lit (-1))]]) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))

abbrev cos_pi_8 : Prop :=
  Nary.cos (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 8) (Nary.lit (-1))]) = Nary.Pow (Nary.Add [Nary.Pow (Nary.lit 2) (Nary.lit (-1)), Nary.Mul [Nary.Pow (Nary.lit 2) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 4) (Nary.lit (-1))]]) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))

abbrev cos_pi_6 : Prop :=
  Nary.cos (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 6) (Nary.lit (-1))]) = Nary.Mul [Nary.Pow (Nary.lit 2) (Nary.lit (-1)), Nary.Pow (Nary.lit 3) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]

abbrev cos_pi_5 : Prop :=
  Nary.cos (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 5) (Nary.lit (-1))]) = Nary.Add [Nary.Pow (Nary.lit 4) (Nary.lit (-1)), Nary.Mul [Nary.Pow (Nary.lit 5) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 4) (Nary.lit (-1))]]

abbrev cos_pi_4 : Prop :=
  Nary.cos (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 4) (Nary.lit (-1))]) = Nary.Mul [Nary.Pow (Nary.lit 2) (Nary.lit (-1)), Nary.Pow (Nary.lit 2) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]

abbrev cos_3pi_10 : Prop :=
  Nary.cos (Nary.Mul [Nary.lit 3, Nary.pi, Nary.Pow (Nary.lit 10) (Nary.lit (-1))]) = Nary.Pow (Nary.Add [Nary.Mul [Nary.lit 5, Nary.Pow (Nary.lit 8) (Nary.lit (-1))], Nary.Mul [Nary.lit (-1), Nary.Mul [Nary.Pow (Nary.lit 5) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 8) (Nary.lit (-1))]]]) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))

abbrev cos_pi_3 : Prop :=
  Nary.cos (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 3) (Nary.lit (-1))]) = Nary.Pow (Nary.lit 2) (Nary.lit (-1))

abbrev cos_3pi_8 : Prop :=
  Nary.cos (Nary.Mul [Nary.lit 3, Nary.pi, Nary.Pow (Nary.lit 8) (Nary.lit (-1))]) = Nary.Pow (Nary.Add [Nary.Pow (Nary.lit 2) (Nary.lit (-1)), Nary.Mul [Nary.lit (-1), Nary.Mul [Nary.Pow (Nary.lit 2) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 4) (Nary.lit (-1))]]]) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))

abbrev cos_2pi_5 : Prop :=
  Nary.cos (Nary.Mul [Nary.lit 2, Nary.pi, Nary.Pow (Nary.lit 5) (Nary.lit (-1))]) = Nary.Add [Nary.Mul [Nary.Pow (Nary.lit 5) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 4) (Nary.lit (-1))], Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 4) (Nary.lit (-1))]]

abbrev cos_5pi_12 : Prop :=
  Nary.cos (Nary.Mul [Nary.lit 5, Nary.pi, Nary.Pow (Nary.lit 12) (Nary.lit (-1))]) = Nary.Mul [Nary.Add [Nary.Pow (Nary.lit 6) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 2) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]], Nary.Pow (Nary.lit 4) (Nary.lit (-1))]

abbrev cos_pi_2 : Prop :=
  Nary.cos (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 2) (Nary.lit (-1))]) = Nary.lit 0

abbrev pythagoras : Prop :=
  ∀ (a : Nary.Number), a ≠ none → Nary.Add [Nary.Pow (Nary.sin a) (Nary.lit 2), Nary.Pow (Nary.cos a) (Nary.lit 2)] = Nary.lit 1

abbrev pythagoras_scaled : Prop :=
  ∀ (b a : Nary.Number), a ≠ none → Nary.Add [Nary.Mul [b, Nary.Pow (Nary.sin a) (Nary.lit 2)], Nary.Mul [b, Nary.Pow (Nary.cos a) (Nary.lit 2)]] = b

abbrev one_minus_sin_squared : Prop :=
  ∀ (a : Nary.Number), Nary.Add [Nary.lit 1, Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.sin a) (Nary.lit 2)]] = Nary.Pow (Nary.cos a) (Nary.lit 2)

abbrev one_minus_cos_squared : Prop :=
  ∀ (a : Nary.Number), Nary.Add [Nary.lit 1, Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.cos a) (Nary.lit 2)]] = Nary.Pow (Nary.sin a) (Nary.lit 2)

abbrev tan_minus_pi : Prop :=
  ∀ (cs : List Nary.Number), Nary.Holds (Nary.Gt (Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.lit 1]]) (Nary.lit 0)) → Nary.tan (Nary.Mul ([Nary.pi] ++ cs)) = Nary.tan (Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.lit 1]], Nary.pi])

abbrev tan_reflect : Prop :=
  ∀ (cs : List Nary.Number), Nary.Holds (Nary.And [Nary.Gt (Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 2) (Nary.lit (-1))]]) (Nary.lit 0), Nary.Le (Nary.Mul cs) (Nary.lit 1)]) → Nary.tan (Nary.Mul ([Nary.pi] ++ cs)) = Nary.Mul [Nary.lit (-1), Nary.tan (Nary.Mul [Nary.Add [Nary.lit 1, Nary.Mul [Nary.lit (-1), Nary.Mul cs]], Nary.pi])]

abbrev tan_period_down : Prop :=
  ∀ (b : Nary.Number) (cs rest : List Nary.Number), Nary.Holds (Nary.Ge (Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.lit 1]]) (Nary.lit 0)) → Nary.tan (Nary.Add ([Nary.Mul ([Nary.pi] ++ cs), b] ++ rest)) = Nary.tan (Nary.Add ([Nary.Mul [Nary.Add [Nary.Mul cs, Nary.Mul [Nary.lit (-1), Nary.lit 1]], Nary.pi], b] ++ rest))

abbrev tan_period_up : Prop :=
  ∀ (b : Nary.Number) (cs rest : List Nary.Number), Nary.Holds (Nary.Lt (Nary.Add [Nary.Mul cs, Nary.Pow (Nary.lit 2) (Nary.lit (-1))]) (Nary.lit 0)) → Nary.tan (Nary.Add ([Nary.Mul ([Nary.pi] ++ cs), b] ++ rest)) = Nary.tan (Nary.Add ([Nary.Mul [Nary.Add [Nary.Mul cs, Nary.lit 1], Nary.pi], b] ++ rest))

abbrev tan_odd : Prop :=
  ∀ (c : Nary.Number) (rest : List Nary.Number), Nary.Holds (Nary.Lt (Nary.exp c) (Nary.lit 1)) → Nary.tan (Nary.Mul ([c] ++ rest)) = Nary.Mul [Nary.lit (-1), Nary.tan (Nary.Mul [Nary.lit (-1), Nary.Mul ([c] ++ rest)])]

abbrev tan_odd_two_negative_terms : Prop :=
  ∀ (c d : Nary.Number) (r1 r2 : List Nary.Number), Nary.Holds (Nary.And [Nary.Lt (Nary.exp c) (Nary.lit 1), Nary.Lt (Nary.exp d) (Nary.lit 1)]) → Nary.tan (Nary.Add [Nary.Mul ([c] ++ r1), Nary.Mul ([d] ++ r2)]) = Nary.Mul [Nary.lit (-1), Nary.tan (Nary.Mul [Nary.lit (-1), Nary.Add [Nary.Mul ([c] ++ r1), Nary.Mul ([d] ++ r2)]])]

abbrev tan_odd_two_of_three_negative : Prop :=
  ∀ (c d b : Nary.Number) (r1 r2 : List Nary.Number), Nary.Holds (Nary.And [Nary.Lt (Nary.exp c) (Nary.lit 1), Nary.Lt (Nary.exp d) (Nary.lit 1)]) → Nary.tan (Nary.Add [Nary.Mul ([c] ++ r1), Nary.Mul ([d] ++ r2), b]) = Nary.Mul [Nary.lit (-1), Nary.tan (Nary.Mul [Nary.lit (-1), Nary.Add [Nary.Mul ([c] ++ r1), Nary.Mul ([d] ++ r2), b]])]

abbrev tan_odd_number_minus_term : Prop :=
  ∀ (n c d : Nary.Number) (r1 : List Nary.Number), Nary.Holds (Nary.And [Nary.Gt (Nary.exp n) (Nary.lit 1), Nary.Lt (Nary.exp c) (Nary.lit 1)]) → Nary.tan (Nary.Add [n, Nary.Mul ([c, d] ++ r1)]) = Nary.Mul [Nary.lit (-1), Nary.tan (Nary.Mul [Nary.lit (-1), Nary.Add [n, Nary.Mul ([c, d] ++ r1)]])]

abbrev tan_zero : Prop :=
  Nary.tan (Nary.lit 0) = Nary.lit 0

abbrev tan_pi_12 : Prop :=
  Nary.tan (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 12) (Nary.lit (-1))]) = Nary.Add [Nary.lit 2, Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.lit 3) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]]

abbrev tan_pi_10 : Prop :=
  Nary.tan (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 10) (Nary.lit (-1))]) = Nary.Pow (Nary.Add [Nary.lit 1, Nary.Mul [Nary.lit (-1), Nary.Mul [Nary.Mul [Nary.lit 2, Nary.Pow (Nary.lit 5) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))], Nary.Pow (Nary.lit 5) (Nary.lit (-1))]]]) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))

abbrev tan_pi_8 : Prop :=
  Nary.tan (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 8) (Nary.lit (-1))]) = Nary.Add [Nary.Pow (Nary.lit 2) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Mul [Nary.lit (-1), Nary.lit 1]]

abbrev tan_pi_6 : Prop :=
  Nary.tan (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 6) (Nary.lit (-1))]) = Nary.Mul [Nary.Pow (Nary.lit 3) (Nary.Pow (Nary.lit 2) (Nary.lit (-1))), Nary.Pow (Nary.lit 3) (Nary.lit (-1))]

abbrev tan_pi_5 : Prop :=
  Nary.tan (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 5) (Nary.lit (-1))]) = Nary.Pow (Nary.Add [Nary.lit 5, Nary.Mul [Nary.lit (-1), Nary.Mul [Nary.lit 2, Nary.Pow (Nary.lit 5) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]]]) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))

abbrev tan_pi_4 : Prop :=
  Nary.tan (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 4) (Nary.lit (-1))]) = Nary.lit 1

abbrev tan_3pi_10 : Prop :=
  Nary.tan (Nary.Mul [Nary.lit 3, Nary.pi, Nary.Pow (Nary.lit 10) (Nary.lit (-1))]) = Nary.Pow (Nary.Add [Nary.lit 1, Nary.Mul [Nary.Mul [Nary.lit 2, Nary.Pow (Nary.lit 5) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))], Nary.Pow (Nary.lit 5) (Nary.lit (-1))]]) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))

abbrev tan_pi_3 : Prop :=
  Nary.tan (Nary.Mul [Nary.pi, Nary.Pow (Nary.lit 3) (Nary.lit (-1))]) = Nary.Pow (Nary.lit 3) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))

abbrev tan_3pi_8 : Prop :=
  Nary.tan (Nary.Mul [Nary.lit 3, Nary.pi, Nary.Pow (Nary.lit 8) (Nary.lit (-1))]) = Nary.Add [Nary.lit 1, Nary.Pow (Nary.lit 2) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]

abbrev tan_2pi_5 : Prop :=
  Nary.tan (Nary.Mul [Nary.lit 2, Nary.pi, Nary.Pow (Nary.lit 5) (Nary.lit (-1))]) = Nary.Pow (Nary.Add [Nary.lit 5, Nary.Mul [Nary.lit 2, Nary.Pow (Nary.lit 5) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]]) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))

abbrev tan_5pi_12 : Prop :=
  Nary.tan (Nary.Mul [Nary.lit 5, Nary.pi, Nary.Pow (Nary.lit 12) (Nary.lit (-1))]) = Nary.Add [Nary.lit 2, Nary.Pow (Nary.lit 3) (Nary.Pow (Nary.lit 2) (Nary.lit (-1)))]

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
  ∀ (a b : Nary.Number) (rest : List Nary.Number), Nary.re (Nary.Add ([a, b] ++ rest)) = Nary.Add [Nary.re a, Nary.re (Nary.Add ([b] ++ rest))]

abbrev re_real_factor : Prop :=
  ∀ (a b : Nary.Number) (rest : List Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → Nary.re (Nary.Mul ([a, b] ++ rest)) = Nary.Mul [a, Nary.re (Nary.Mul ([b] ++ rest))]

abbrev re_exp_real : Prop :=
  ∀ (a : Nary.Number), Nary.Holds (Nary.Eq (Nary.re a) a) → Nary.re (Nary.exp a) = Nary.exp a

abbrev derivative_sin : Prop :=
  Nary.Derivative (fun z => Nary.sin (some z)) = fun z => Nary.cos (some z)

abbrev derivative_exp : Prop :=
  Nary.Derivative (fun z => Nary.exp (some z)) = fun z => Nary.exp (some z)

end Nary.ElementaryRules.Statement
