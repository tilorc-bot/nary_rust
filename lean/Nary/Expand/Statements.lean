import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.Expand.Statement

abbrev expand_distribute : Prop :=
  ∀ (a b c : Nary.Number) (cs : List Nary.Number), Nary.Mul [a, Nary.Add ([b, c] ++ cs)] = Nary.Add [Nary.Mul [a, b], Nary.Mul [a, Nary.Add ([c] ++ cs)]]

abbrev expand_power_of_sum : Prop :=
  ∀ (a b n : Nary.Number) (cs : List Nary.Number), Nary.Holds (Nary.And [Nary.Eq (Nary.exp (Nary.Mul [Nary.Mul [Nary.Mul [Nary.lit 2, Nary.pi], Nary.I], n])) (Nary.lit 1), Nary.Gt n (Nary.lit 1)]) → Nary.Pow (Nary.Add ([a, b] ++ cs)) n = Nary.Add [Nary.Mul [a, Nary.Pow (Nary.Add ([a, b] ++ cs)) (Nary.Add [n, Nary.Mul [Nary.lit (-1), Nary.lit 1]])], Nary.Mul [Nary.Add ([b] ++ cs), Nary.Pow (Nary.Add ([a, b] ++ cs)) (Nary.Add [n, Nary.Mul [Nary.lit (-1), Nary.lit 1]])]]

abbrev expand_reciprocal_power_of_sum : Prop :=
  ∀ (a b n : Nary.Number) (cs : List Nary.Number), Nary.Holds (Nary.And [Nary.Eq (Nary.exp (Nary.Mul [Nary.Mul [Nary.Mul [Nary.lit 2, Nary.pi], Nary.I], n])) (Nary.lit 1), Nary.Lt n (Nary.lit (-1))]) → Nary.Pow (Nary.Add ([a, b] ++ cs)) n = Nary.Pow (Nary.Pow (Nary.Add ([a, b] ++ cs)) (Nary.Mul [Nary.lit (-1), n])) (Nary.lit (-1))

abbrev expand_exp_sum : Prop :=
  ∀ (a b : Nary.Number) (cs : List Nary.Number), Nary.exp (Nary.Add ([a, b] ++ cs)) = Nary.Mul [Nary.exp a, Nary.exp (Nary.Add ([b] ++ cs))]

abbrev expand_log_positive_factor : Prop :=
  ∀ (a b : Nary.Number) (cs : List Nary.Number), Nary.Holds (Nary.Gt a (Nary.lit 0)) → Nary.log (Nary.Mul ([a, b] ++ cs)) = Nary.Add [Nary.log a, Nary.log (Nary.Mul ([b] ++ cs))]

abbrev expand_log_negative_pair : Prop :=
  ∀ (a b : Nary.Number) (cs : List Nary.Number), Nary.Holds (Nary.And [Nary.Lt a (Nary.lit 0), Nary.Lt b (Nary.lit 0)]) → Nary.log (Nary.Mul ([a, b] ++ cs)) = Nary.Add [Nary.Add [Nary.log (Nary.Mul [Nary.lit (-1), a]), Nary.log (Nary.Mul [Nary.lit (-1), b])], Nary.log (Nary.Mul cs)]

abbrev expand_log_negative_factor : Prop :=
  ∀ (a b : Nary.Number) (cs : List Nary.Number), Nary.Holds (Nary.And [Nary.Lt a (Nary.lit 0), Nary.Ne a (Nary.lit (-1))]) → Nary.log (Nary.Mul ([a, b] ++ cs)) = Nary.Add [Nary.log (Nary.Mul [Nary.lit (-1), a]), Nary.log (Nary.Mul [Nary.lit (-1), Nary.Mul ([b] ++ cs)])]

abbrev expand_log_root : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.And [Nary.Eq (Nary.re b) b, Nary.Gt b (Nary.lit (-1)), Nary.Le b (Nary.lit 1)]) → Nary.log (Nary.Pow a b) = Nary.Mul [b, Nary.log a]

end Nary.Expand.Statement
