import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.Logcombine.Statement

abbrev logcombine_sum : Prop :=
  ∀ (a b : Nary.Number), Nary.Holds (Nary.And [Nary.Gt a (Nary.lit 0), Nary.Gt b (Nary.lit 0)]) → Nary.Add [Nary.log a, Nary.log b] = Nary.log (Nary.Mul [a, b])

end Nary.Logcombine.Statement
