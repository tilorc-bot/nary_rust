import Nary.Calculus
import Nary.Facts
import Nary.Logic

namespace Nary.ExpandTrig.Statement

abbrev expand_trig_sin_sum : Prop :=
  ∀ (a b : Nary.Number) (cs : List Nary.Number), Nary.sin (Nary.Add ([a, b] ++ cs)) = Nary.Add [Nary.Mul [Nary.sin a, Nary.cos (Nary.Add ([b] ++ cs))], Nary.Mul [Nary.sin (Nary.Add ([b] ++ cs)), Nary.cos a]]

abbrev expand_trig_cos_sum : Prop :=
  ∀ (a b : Nary.Number) (cs : List Nary.Number), Nary.cos (Nary.Add ([a, b] ++ cs)) = Nary.Add [Nary.Mul [Nary.cos a, Nary.cos (Nary.Add ([b] ++ cs))], Nary.Mul [Nary.lit (-1), Nary.Mul [Nary.sin a, Nary.sin (Nary.Add ([b] ++ cs))]]]

abbrev expand_trig_sin_double : Prop :=
  ∀ (a : Nary.Number), Nary.sin (Nary.Mul [Nary.lit 2, a]) = Nary.Mul [Nary.lit 2, Nary.sin a, Nary.cos a]

abbrev expand_trig_cos_double : Prop :=
  ∀ (a : Nary.Number), Nary.cos (Nary.Mul [Nary.lit 2, a]) = Nary.Add [Nary.Mul [Nary.lit 2, Nary.Pow (Nary.cos a) (Nary.lit 2)], Nary.Mul [Nary.lit (-1), Nary.lit 1]]

abbrev expand_trig_sin_triple : Prop :=
  ∀ (a : Nary.Number), Nary.sin (Nary.Mul [Nary.lit 3, a]) = Nary.Add [Nary.Mul [Nary.lit 3, Nary.sin a], Nary.Mul [Nary.lit (-1), Nary.Mul [Nary.lit 4, Nary.Pow (Nary.sin a) (Nary.lit 3)]]]

abbrev expand_trig_cos_triple : Prop :=
  ∀ (a : Nary.Number), Nary.cos (Nary.Mul [Nary.lit 3, a]) = Nary.Add [Nary.Mul [Nary.lit 4, Nary.Pow (Nary.cos a) (Nary.lit 3)], Nary.Mul [Nary.lit (-1), Nary.Mul [Nary.lit 3, Nary.cos a]]]

end Nary.ExpandTrig.Statement
