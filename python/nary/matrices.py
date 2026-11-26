"""For a Matrix, + builds MatAdd and * builds MatMul.

    >>> from nary import NumberKind
    >>> from nary.matrices import Determinant, Matrix, Transpose
    >>> A, B = Matrix("A"), Matrix("B")
    >>> x = NumberKind("x")
    >>> Transpose(A + B) * A
    MatMul(Transpose(MatAdd(A, B)), A)

Determinant returns a number.

    >>> Determinant(A * B) + x
    Add(Determinant(MatMul(A, B)), x)

A number is not accepted where a matrix is expected.

    >>> Determinant(x)
    Traceback (most recent call last):
        ...
    TypeError: Determinant expects MatrixKind(NumberKind), got NumberKind: x
"""

from ._core import ManyAlike, declare_kind_family, set_operator
from .domains import declare_function
from .kinds import NumberKind

__all__ = [
    "MatrixKind", "Matrix",
    "MatAdd", "MatMul", "Transpose", "Inverse", "Determinant", "Trace",
]

MatrixKind = declare_kind_family("MatrixKind", params=1)

Matrix = MatrixKind(NumberKind)

terms, factors, arg = Matrix("terms"), Matrix("factors"), Matrix("arg")

MatAdd = declare_function("MatAdd", ManyAlike(terms), returns=Matrix, domain=None)
MatMul = declare_function("MatMul", ManyAlike(factors), returns=Matrix, domain=None)
Transpose = declare_function("Transpose", arg, returns=Matrix, domain=None)
Inverse = declare_function("Inverse", arg, returns=Matrix, domain=None)
Determinant = declare_function("Determinant", arg, returns=NumberKind, domain=None)
Trace = declare_function("Trace", arg, returns=NumberKind, domain=None)

set_operator(Matrix, "+", MatAdd)
set_operator(Matrix, "*", MatMul)
