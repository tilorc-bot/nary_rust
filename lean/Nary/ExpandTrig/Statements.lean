import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.ExpandTrig.Statement

abbrev expand_trig_sin_double : Prop :=
  ∀ (a : Nary.Number), Nary.sin (Nary.Mul [Nary.lit 2, a]) = Nary.Mul [Nary.lit 2, Nary.sin a, Nary.cos a]

abbrev expand_trig_cos_double : Prop :=
  ∀ (a : Nary.Number), Nary.cos (Nary.Mul [Nary.lit 2, a]) = Nary.Add [Nary.Pow (Nary.cos a) (Nary.lit 2), Nary.Mul [Nary.lit (-1), Nary.Pow (Nary.sin a) (Nary.lit 2)]]

end Nary.ExpandTrig.Statement
