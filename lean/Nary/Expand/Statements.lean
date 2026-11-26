import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.Expand.Statement

abbrev expand_distribute : Prop :=
  ∀ (a b c : Nary.Number) (cs : List Nary.Number), Nary.Mul [a, Nary.Add ([b, c] ++ cs)] = Nary.Add [Nary.Mul [a, b], Nary.Mul [a, Nary.Add ([c] ++ cs)]]

abbrev expand_square : Prop :=
  ∀ (a b : Nary.Number), Nary.Pow (Nary.Add [a, b]) (Nary.lit 2) = Nary.Add [Nary.Add [Nary.Pow a (Nary.lit 2), Nary.Mul [Nary.Mul [Nary.lit 2, a], b]], Nary.Pow b (Nary.lit 2)]

end Nary.Expand.Statement
