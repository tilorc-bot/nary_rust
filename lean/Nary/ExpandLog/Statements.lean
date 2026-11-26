import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.ExpandLog.Statement

abbrev expand_log_product : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.And [Nary.Gt a (Nary.lit 0), Nary.Gt b (Nary.lit 0)]) → Nary.log (Nary.Mul [a, b]) = Nary.Add [Nary.log a, Nary.log b]

end Nary.ExpandLog.Statement
