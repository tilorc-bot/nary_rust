from nary import E, Add, Eq, FunctionKind, Ge, Gt, Mul, NumberKind, Pow, cos, exp, log, re, sin, tan
from nary.logic import And, Not, Or, true

SOURCE = "satsimp bd34c0a25506be91845ca7a85e8fa9b2e8466b32"
SYMPY = "1.14.0"

F = FunctionKind((NumberKind,), NumberKind)("F")
a = NumberKind("a")
b = NumberKind("b")
d = NumberKind("d")
e = NumberKind("e")
p = NumberKind("p")
t = NumberKind("t")
u = NumberKind("u")
v = NumberKind("v")
x = NumberKind("x")

REFINE = {
    re: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
            (re(u), u, Or(Eq(re(u), u), Eq(re(u), u))),
            (Mul(Pow(-1, a), Pow(-1, e)), Pow(-1, Add(a, e)), true),
        ]),
    ],
    Mul: [
        ("rule", (), [
            (Mul(Pow(-1, a), Pow(-1, e)), Pow(-1, Add(a, e)), true),
        ]),
    ],
    log: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
        ]),
    ],
    Pow: [
        ("rule", (), [
            (Pow(E, x), exp(x), true),
            (Pow(Pow(b, p), e), Pow(b, Mul(e, p)), And(Gt(p, 0), Or(Ge(b, 0), Ge(b, 0)))),
            (Pow(Pow(p, t), e), Pow(p, Mul(e, t)), And(Gt(p, 0), Eq(re(t), t))),
            (Pow(0, p), 0, Gt(p, 0)),
            (exp(Mul(e, log(b))), Pow(b, e), Or(Gt(e, 0), Not(Eq(b, 0)))),
        ]),
        ("identity", (log,), [
            (Pow(d, e), exp(Mul(e, log(d))), Not(Eq(d, 0))),
        ]),
    ],
    exp: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
        ]),
        ("rule", (), [
            (Pow(E, x), exp(x), true),
            (Pow(Pow(b, p), e), Pow(b, Mul(e, p)), And(Gt(p, 0), Or(Ge(b, 0), Ge(b, 0)))),
            (Pow(Pow(p, t), e), Pow(p, Mul(e, t)), And(Gt(p, 0), Eq(re(t), t))),
            (Pow(0, p), 0, Gt(p, 0)),
            (exp(Mul(e, log(b))), Pow(b, e), Or(Gt(e, 0), Not(Eq(b, 0)))),
        ]),
        ("identity", (), [
            (exp(Add(a, b)), Mul(exp(a), exp(b)), true),
        ]),
    ],
    sin: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
        ]),
    ],
    cos: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
        ]),
    ],
    tan: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
        ]),
    ],
}

TRIGSIMP = {
    "normalize": ("rule", (), [
        (tan(u), Mul(Pow(cos(u), -1), sin(u)), true),
    ]),
    "conditional": ("rule", (), [
    ]),
    "quotients": ("rule", (), [
    ]),
    "pythagorean": ("substitution", (), [
        (Pow(sin(u), 2), Add(1, Mul(-1, Pow(cos(u), 2))), true),
        (Pow(cos(u), 2), Add(1, Mul(-1, Pow(sin(u), 2))), true),
    ]),
    "substitutions": ("substitution", (), [
        (Mul(Pow(cos(u), -1), sin(u)), tan(u), true),
        (Pow(sin(u), 2), Add(1, Mul(-1, Pow(cos(u), 2))), true),
        (Pow(cos(u), 2), Add(1, Mul(-1, Pow(sin(u), 2))), true),
        (Pow(cos(u), -2), Add(1, Pow(tan(u), 2)), true),
        (Pow(tan(u), 2), Add(-1, Pow(cos(u), -2)), true),
        (Mul(cos(u), sin(u)), Mul(Pow(2, -1), sin(Mul(2, u))), true),
        (Pow(sin(u), 2), Add(Pow(2, -1), Mul(Mul(-1, Pow(2, -1)), cos(Mul(2, u)))), true),
        (Pow(cos(u), 2), Add(Pow(2, -1), Mul(Pow(2, -1), cos(Mul(2, u)))), true),
        (Mul(cos(v), sin(u)), Add(Mul(-1, cos(u), sin(v)), sin(Add(u, v))), true),
        (Mul(cos(v), sin(u)), Add(Mul(cos(u), sin(v)), sin(Add(u, Mul(-1, v)))), true),
        (Mul(cos(u), cos(v)), Add(Mul(sin(u), sin(v)), cos(Add(u, v))), true),
        (Mul(cos(u), cos(v)), Add(Mul(-1, sin(u), sin(v)), cos(Add(u, Mul(-1, v)))), true),
        (Mul(sin(u), sin(v)), Add(Mul(-1, cos(u), cos(v)), cos(Add(u, Mul(-1, v)))), true),
        (Mul(sin(u), sin(v)), Add(Mul(-1, cos(Add(u, v))), Mul(cos(u), cos(v))), true),
        (sin(Add(u, v)), Add(Mul(cos(u), sin(v)), Mul(cos(v), sin(u))), true),
        (cos(Add(u, v)), Add(Mul(cos(u), cos(v)), Mul(-1, sin(u), sin(v))), true),
        (sin(Mul(2, u)), Mul(2, cos(u), sin(u)), true),
        (cos(Mul(2, u)), Add(Pow(cos(u), 2), Mul(-1, Pow(sin(u), 2))), true),
        (cos(Mul(2, u)), Add(1, Mul(-2, Pow(sin(u), 2))), true),
        (cos(Mul(2, u)), Add(-1, Mul(2, Pow(cos(u), 2))), true),
    ]),
}

TRIG_HEADS = (sin, cos, tan)
