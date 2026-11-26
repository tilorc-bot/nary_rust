import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.LogPower.Statement

abbrev log_pow : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.And [Nary.Gt a (Nary.lit 0), Nary.Eq (Nary.re b) b]) → Nary.log (Nary.Pow a b) = Nary.Mul [b, Nary.log a]

end Nary.LogPower.Statement
