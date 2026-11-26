import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.ExpandLog.Statement

abbrev expand_log_positive_factor : Prop :=
  ∀ (a b : Nary.Number) (cs : List Nary.Number), Nary.Holds (Nary.Gt a (Nary.lit 0)) → Nary.log (Nary.Mul ([a, b] ++ cs)) = Nary.Add [Nary.log a, Nary.log (Nary.Mul ([b] ++ cs))]

abbrev expand_log_negative_pair : Prop :=
  ∀ (a b : Nary.Number) (cs : List Nary.Number), Nary.Holds (Nary.And [Nary.Lt a (Nary.lit 0), Nary.Lt b (Nary.lit 0)]) → Nary.log (Nary.Mul ([a, b] ++ cs)) = Nary.Add [Nary.Add [Nary.log (Nary.Mul [Nary.lit (-1), a]), Nary.log (Nary.Mul [Nary.lit (-1), b])], Nary.log (Nary.Mul cs)]

abbrev expand_log_negative_factor : Prop :=
  ∀ (a b : Nary.Number) (cs : List Nary.Number), Nary.Holds (Nary.And [Nary.Lt a (Nary.lit 0), Nary.Ne a (Nary.lit (-1))]) → Nary.log (Nary.Mul ([a, b] ++ cs)) = Nary.Add [Nary.log (Nary.Mul [Nary.lit (-1), a]), Nary.log (Nary.Mul [Nary.lit (-1), Nary.Mul ([b] ++ cs)])]

abbrev expand_log_root : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.And [Nary.Eq (Nary.re b) b, Nary.Gt b (Nary.lit (-1)), Nary.Le b (Nary.lit 1)]) → Nary.log (Nary.Pow a b) = Nary.Mul [b, Nary.log a]

end Nary.ExpandLog.Statement
