"""Facts decides conditions from known facts, and can be the known of rewrite.

    >>> from nary import Gt, Ne, NumberKind, log
    >>> from nary.deciding import Facts
    >>> x, y, z = NumberKind("x"), NumberKind("y"), NumberKind("z")
    >>> known = Facts([Gt(x, 0), Gt(y, 0), Gt(z, 1)])
    >>> known(Gt(x * y + z, 1)), known(Ne(log(z), 0)), known(Gt(x - z, 0))
    (True, True, False)
    >>> from nary.arithmetic_rules import rules
    >>> from nary.rewriting import rewrite
    >>> rewrite((x + 1) / (x + 1), rules, known=known)
    1
"""

from ._facts import Facts

__all__ = ["Facts"]
