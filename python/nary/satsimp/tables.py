from nary import E, I, Abs, Add, Eq, FunctionKind, Ge, Gt, Le, Lt, Mul, NumberKind, Pow, arg, ceiling, conjugate, cos, cosh, exp, floor, im, log, pi, re, sign, sin, sinh, tan, tanh
from nary.logic import And, Not, Or, true

SOURCE = "satsimp bd34c0a25506be91845ca7a85e8fa9b2e8466b32"
SYMPY = "1.14.0"

F = FunctionKind((NumberKind,), NumberKind)("F")
a = NumberKind("a")
b = NumberKind("b")
d = NumberKind("d")
e = NumberKind("e")
f = NumberKind("f")
p = NumberKind("p")
r = NumberKind("r")
t = NumberKind("t")
u = NumberKind("u")
v = NumberKind("v")
w = NumberKind("w")
x = NumberKind("x")
y = NumberKind("y")
z = NumberKind("z")

REFINE = {
    Abs: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
            (Abs(a), a, Or(Ge(a, 0), Ge(a, 0))),
            (Abs(a), Mul(-1, a), Or(Le(a, 0), Le(a, 0))),
            (re(u), u, Or(Eq(re(u), u), Eq(re(u), u))),
            (im(u), 0, Or(Eq(re(u), u), Eq(re(u), u))),
            (sign(a), 1, Or(Gt(a, 0), Gt(a, 0))),
            (sign(a), -1, Or(Lt(a, 0), Lt(a, 0))),
            (sign(Abs(d)), 1, Not(Eq(d, 0))),
            (sign(exp(z)), 1, Eq(re(z), z)),
            (conjugate(u), u, Or(Eq(re(u), u), Eq(re(u), u))),
            (conjugate(exp(z)), exp(conjugate(z)), true),
            (conjugate(Pow(b, e)), Pow(b, conjugate(e)), Gt(b, 0)),
            (Mul(Pow(-1, a), Pow(-1, e)), Pow(-1, Add(a, e)), true),
        ]),
        ("identity", (floor, im, arg), [
            (Abs(exp(z)), exp(re(z)), true),
            (Abs(Pow(b, e)), exp(re(Mul(e, log(b)))), Or(Gt(e, 0), Not(Eq(b, 0)))),
            (Abs(Mul(r, y)), Mul(Abs(r), Abs(y)), true),
            (Abs(Mul(r, y)), Mul(Abs(r), Abs(y)), true),
        ]),
        ("identity", (sign,), [
            (Abs(f), Mul(f, Pow(sign(f), -1)), And(true, Not(Eq(f, 0)))),
        ]),
    ],
    re: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
            (Abs(a), a, Or(Ge(a, 0), Ge(a, 0))),
            (Abs(a), Mul(-1, a), Or(Le(a, 0), Le(a, 0))),
            (re(u), u, Or(Eq(re(u), u), Eq(re(u), u))),
            (im(u), 0, Or(Eq(re(u), u), Eq(re(u), u))),
            (sign(a), 1, Or(Gt(a, 0), Gt(a, 0))),
            (sign(a), -1, Or(Lt(a, 0), Lt(a, 0))),
            (sign(Abs(d)), 1, Not(Eq(d, 0))),
            (sign(exp(z)), 1, Eq(re(z), z)),
            (conjugate(u), u, Or(Eq(re(u), u), Eq(re(u), u))),
            (conjugate(exp(z)), exp(conjugate(z)), true),
            (conjugate(Pow(b, e)), Pow(b, conjugate(e)), Gt(b, 0)),
            (Mul(Pow(-1, a), Pow(-1, e)), Pow(-1, Add(a, e)), true),
        ]),
    ],
    im: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
            (Abs(a), a, Or(Ge(a, 0), Ge(a, 0))),
            (Abs(a), Mul(-1, a), Or(Le(a, 0), Le(a, 0))),
            (re(u), u, Or(Eq(re(u), u), Eq(re(u), u))),
            (im(u), 0, Or(Eq(re(u), u), Eq(re(u), u))),
            (sign(a), 1, Or(Gt(a, 0), Gt(a, 0))),
            (sign(a), -1, Or(Lt(a, 0), Lt(a, 0))),
            (sign(Abs(d)), 1, Not(Eq(d, 0))),
            (sign(exp(z)), 1, Eq(re(z), z)),
            (conjugate(u), u, Or(Eq(re(u), u), Eq(re(u), u))),
            (conjugate(exp(z)), exp(conjugate(z)), true),
            (conjugate(Pow(b, e)), Pow(b, conjugate(e)), Gt(b, 0)),
            (Mul(Pow(-1, a), Pow(-1, e)), Pow(-1, Add(a, e)), true),
        ]),
    ],
    arg: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
            (Abs(a), a, Or(Ge(a, 0), Ge(a, 0))),
            (Abs(a), Mul(-1, a), Or(Le(a, 0), Le(a, 0))),
            (re(u), u, Or(Eq(re(u), u), Eq(re(u), u))),
            (im(u), 0, Or(Eq(re(u), u), Eq(re(u), u))),
            (sign(a), 1, Or(Gt(a, 0), Gt(a, 0))),
            (sign(a), -1, Or(Lt(a, 0), Lt(a, 0))),
            (sign(Abs(d)), 1, Not(Eq(d, 0))),
            (sign(exp(z)), 1, Eq(re(z), z)),
            (conjugate(u), u, Or(Eq(re(u), u), Eq(re(u), u))),
            (conjugate(exp(z)), exp(conjugate(z)), true),
            (conjugate(Pow(b, e)), Pow(b, conjugate(e)), Gt(b, 0)),
            (Mul(Pow(-1, a), Pow(-1, e)), Pow(-1, Add(a, e)), true),
        ]),
        ("identity", (floor, im), [
            (arg(exp(z)), Add(Mul(2, pi, floor(Add(Pow(2, -1), Mul(Mul(-1, Pow(2, -1)), Pow(pi, -1), im(z))))), im(z)), true),
            (arg(Mul(r, y)), Add(Mul(2, pi, floor(Add(Pow(2, -1), Mul(Mul(-1, Pow(2, -1)), Pow(pi, -1), Add(arg(r), arg(y)))))), arg(r), arg(y)), true),
            (arg(Mul(r, y)), Add(Mul(2, pi, floor(Add(Pow(2, -1), Mul(Mul(-1, Pow(2, -1)), Pow(pi, -1), Add(arg(Mul(-1, r)), arg(Mul(-1, y))))))), arg(Mul(-1, r)), arg(Mul(-1, y))), true),
            (arg(conjugate(w)), Add(Mul(-1, arg(w)), Mul(2, pi, floor(Add(Pow(2, -1), Mul(Pow(2, -1), Pow(pi, -1), arg(w)))))), true),
        ]),
        ("identity", (sign,), [
            (arg(d), Mul(-1, I, log(sign(d))), Not(Eq(d, 0))),
        ]),
    ],
    sign: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
            (Abs(a), a, Or(Ge(a, 0), Ge(a, 0))),
            (Abs(a), Mul(-1, a), Or(Le(a, 0), Le(a, 0))),
            (re(u), u, Or(Eq(re(u), u), Eq(re(u), u))),
            (im(u), 0, Or(Eq(re(u), u), Eq(re(u), u))),
            (sign(a), 1, Or(Gt(a, 0), Gt(a, 0))),
            (sign(a), -1, Or(Lt(a, 0), Lt(a, 0))),
            (sign(Abs(d)), 1, Not(Eq(d, 0))),
            (sign(exp(z)), 1, Eq(re(z), z)),
            (conjugate(u), u, Or(Eq(re(u), u), Eq(re(u), u))),
            (conjugate(exp(z)), exp(conjugate(z)), true),
            (conjugate(Pow(b, e)), Pow(b, conjugate(e)), Gt(b, 0)),
            (Mul(Pow(-1, a), Pow(-1, e)), Pow(-1, Add(a, e)), true),
        ]),
        ("identity", (floor, im, arg), [
            (sign(Mul(r, y)), Mul(sign(r), sign(y)), true),
        ]),
    ],
    conjugate: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
            (Abs(a), a, Or(Ge(a, 0), Ge(a, 0))),
            (Abs(a), Mul(-1, a), Or(Le(a, 0), Le(a, 0))),
            (re(u), u, Or(Eq(re(u), u), Eq(re(u), u))),
            (im(u), 0, Or(Eq(re(u), u), Eq(re(u), u))),
            (sign(a), 1, Or(Gt(a, 0), Gt(a, 0))),
            (sign(a), -1, Or(Lt(a, 0), Lt(a, 0))),
            (sign(Abs(d)), 1, Not(Eq(d, 0))),
            (sign(exp(z)), 1, Eq(re(z), z)),
            (conjugate(u), u, Or(Eq(re(u), u), Eq(re(u), u))),
            (conjugate(exp(z)), exp(conjugate(z)), true),
            (conjugate(Pow(b, e)), Pow(b, conjugate(e)), Gt(b, 0)),
            (Mul(Pow(-1, a), Pow(-1, e)), Pow(-1, Add(a, e)), true),
        ]),
    ],
    Mul: [
        ("rule", (), [
            (Mul(Pow(-1, a), Pow(-1, e)), Pow(-1, Add(a, e)), true),
        ]),
    ],
    sinh: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
        ]),
    ],
    cosh: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
        ]),
    ],
    tanh: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
        ]),
    ],
    floor: [
        ("rule", (), [
            (floor(Add(x, ceiling(w))), Add(ceiling(w), floor(x)), true),
            (floor(Add(x, floor(w))), Add(floor(w), floor(x)), true),
        ]),
    ],
    ceiling: [
        ("rule", (), [
            (ceiling(Add(x, ceiling(w))), Add(ceiling(w), ceiling(x)), true),
            (ceiling(Add(x, floor(w))), Add(ceiling(x), floor(w)), true),
        ]),
    ],
    log: [
        ("rule", (), [
            (F(x), F(0), Eq(x, 0)),
        ]),
        ("identity", (floor, im, arg), [
            (log(exp(z)), Add(z, Mul(2, pi, I, floor(Add(Pow(2, -1), Mul(Mul(-1, Pow(2, -1)), Pow(pi, -1), im(z)))))), true),
            (log(Pow(b, e)), Add(Mul(e, log(b)), Mul(2, pi, I, floor(Add(Pow(2, -1), Mul(Mul(-1, Pow(2, -1)), Pow(pi, -1), im(Mul(e, log(b)))))))), And(Or(Gt(e, 0), Not(Eq(b, 0))), Or(true, Gt(e, 0), Eq(re(b), b)))),
            (log(Mul(r, y)), Add(Mul(2, pi, I, floor(Add(Pow(2, -1), Mul(Mul(-1, Pow(2, -1)), Pow(pi, -1), Add(arg(r), arg(y)))))), log(r), log(y)), true),
            (log(Mul(r, y)), Add(Mul(2, pi, I, floor(Add(Pow(2, -1), Mul(Mul(-1, Pow(2, -1)), Pow(pi, -1), Add(arg(Mul(-1, r)), arg(Mul(-1, y))))))), log(Mul(-1, r)), log(Mul(-1, y))), true),
            (log(d), Add(Mul(I, arg(d)), log(Abs(d))), Not(Eq(d, 0))),
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
        ("identity", (floor, im, arg, log), [
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
        ("identity", (floor, im, arg), [
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
        (tanh(u), Mul(Pow(cosh(u), -1), sinh(u)), true),
    ]),
    "conditional": ("rule", (), [
        (Pow(Pow(w, 2), Pow(2, -1)), Abs(w), Eq(re(w), w)),
        (Pow(Pow(w, 2), Mul(-1, Pow(2, -1))), Pow(Abs(w), -1), Eq(re(w), w)),
        (Pow(Pow(w, -2), Pow(2, -1)), Pow(Abs(w), -1), Eq(re(w), w)),
        (Abs(w), w, Ge(w, 0)),
        (Abs(w), Mul(-1, w), Le(w, 0)),
    ]),
    "quotients": ("rule", (), [
    ]),
    "pythagorean": ("substitution", (), [
        (Pow(sin(u), 2), Add(1, Mul(-1, Pow(cos(u), 2))), true),
        (Pow(cos(u), 2), Add(1, Mul(-1, Pow(sin(u), 2))), true),
        (Pow(sinh(u), 2), Add(-1, Pow(cosh(u), 2)), true),
        (Pow(cosh(u), 2), Add(1, Pow(sinh(u), 2)), true),
    ]),
    "substitutions": ("substitution", (), [
        (Mul(Pow(cos(u), -1), sin(u)), tan(u), true),
        (Mul(Pow(cosh(u), -1), sinh(u)), tanh(u), true),
        (Pow(sin(u), 2), Add(1, Mul(-1, Pow(cos(u), 2))), true),
        (Pow(cos(u), 2), Add(1, Mul(-1, Pow(sin(u), 2))), true),
        (Pow(sinh(u), 2), Add(-1, Pow(cosh(u), 2)), true),
        (Pow(cosh(u), 2), Add(1, Pow(sinh(u), 2)), true),
        (Pow(cos(u), -2), Add(1, Pow(tan(u), 2)), true),
        (Pow(tan(u), 2), Add(-1, Pow(cos(u), -2)), true),
        (Pow(cosh(u), -2), Add(1, Mul(-1, Pow(tanh(u), 2))), true),
        (Pow(tanh(u), 2), Add(1, Mul(-1, Pow(cosh(u), -2))), true),
        (Mul(cos(u), sin(u)), Mul(Pow(2, -1), sin(Mul(2, u))), true),
        (Pow(sin(u), 2), Add(Pow(2, -1), Mul(Mul(-1, Pow(2, -1)), cos(Mul(2, u)))), true),
        (Pow(cos(u), 2), Add(Pow(2, -1), Mul(Pow(2, -1), cos(Mul(2, u)))), true),
        (Mul(cos(v), sin(u)), Add(Mul(-1, cos(u), sin(v)), sin(Add(u, v))), true),
        (Mul(cos(v), sin(u)), Add(Mul(cos(u), sin(v)), sin(Add(u, Mul(-1, v)))), true),
        (Mul(cos(u), cos(v)), Add(Mul(sin(u), sin(v)), cos(Add(u, v))), true),
        (Mul(cos(u), cos(v)), Add(Mul(-1, sin(u), sin(v)), cos(Add(u, Mul(-1, v)))), true),
        (Mul(sin(u), sin(v)), Add(Mul(-1, cos(u), cos(v)), cos(Add(u, Mul(-1, v)))), true),
        (Mul(sin(u), sin(v)), Add(Mul(-1, cos(Add(u, v))), Mul(cos(u), cos(v))), true),
        (Mul(cosh(u), sinh(u)), Mul(Pow(2, -1), sinh(Mul(2, u))), true),
        (Pow(sinh(u), 2), Add(Mul(-1, Pow(2, -1)), Mul(Pow(2, -1), cosh(Mul(2, u)))), true),
        (Pow(cosh(u), 2), Add(Pow(2, -1), Mul(Pow(2, -1), cosh(Mul(2, u)))), true),
        (Mul(cosh(v), sinh(u)), Add(Mul(-1, cosh(u), sinh(v)), sinh(Add(u, v))), true),
        (Mul(cosh(v), sinh(u)), Add(Mul(cosh(u), sinh(v)), sinh(Add(u, Mul(-1, v)))), true),
        (Mul(cosh(u), cosh(v)), Add(Mul(-1, sinh(u), sinh(v)), cosh(Add(u, v))), true),
        (Mul(cosh(u), cosh(v)), Add(Mul(sinh(u), sinh(v)), cosh(Add(u, Mul(-1, v)))), true),
        (Mul(sinh(u), sinh(v)), Add(Mul(-1, cosh(u), cosh(v)), cosh(Add(u, v))), true),
        (Mul(sinh(u), sinh(v)), Add(Mul(-1, cosh(Add(u, Mul(-1, v)))), Mul(cosh(u), cosh(v))), true),
        (sin(Add(u, v)), Add(Mul(cos(u), sin(v)), Mul(cos(v), sin(u))), true),
        (cos(Add(u, v)), Add(Mul(cos(u), cos(v)), Mul(-1, sin(u), sin(v))), true),
        (sin(Mul(2, u)), Mul(2, cos(u), sin(u)), true),
        (cos(Mul(2, u)), Add(Pow(cos(u), 2), Mul(-1, Pow(sin(u), 2))), true),
        (cos(Mul(2, u)), Add(1, Mul(-2, Pow(sin(u), 2))), true),
        (cos(Mul(2, u)), Add(-1, Mul(2, Pow(cos(u), 2))), true),
        (sinh(Add(u, v)), Add(Mul(cosh(u), sinh(v)), Mul(cosh(v), sinh(u))), true),
        (cosh(Add(u, v)), Add(Mul(cosh(u), cosh(v)), Mul(sinh(u), sinh(v))), true),
        (sinh(Mul(2, u)), Mul(2, cosh(u), sinh(u)), true),
        (cosh(Mul(2, u)), Add(Pow(cosh(u), 2), Pow(sinh(u), 2)), true),
        (cosh(Mul(2, u)), Add(1, Mul(2, Pow(sinh(u), 2))), true),
        (cosh(Mul(2, u)), Add(-1, Mul(2, Pow(cosh(u), 2))), true),
    ]),
}

TRIG_HEADS = (sin, cos, tan, sinh, cosh, tanh)
