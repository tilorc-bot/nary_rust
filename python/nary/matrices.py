"""Matrices of numbers.

This module declares the kind family ``MatrixKind`` (one parameter, the kind
of the elements) and, for matrices of numbers, the kind
``Matrix = MatrixKind(NumberKind)`` and these functions:

- ``MatAdd(A, B, ...)`` and ``MatMul(A, B, ...)``: any number of matrices,
  returning a matrix.
- ``Transpose(A)`` and ``Inverse(A)``: a matrix, returning a matrix.
- ``Determinant(A)`` and ``Trace(A)``: a matrix, returning a ``NumberKind``.

For a ``Matrix``, ``+`` builds ``MatAdd`` and ``*`` builds ``MatMul``.
Matrix multiplication does not commute, so matrices have their own sum and
product rather than sharing ``Add`` and ``Mul`` with numbers.

The module is imported as ``nary.matrices``; ``import nary`` does not
import it, and its names are not re-exported from ``nary``.

    >>> from nary import NumberKind
    >>> from nary.matrices import Determinant, Matrix, Transpose
    >>> A, B = Matrix("A"), Matrix("B")
    >>> x = NumberKind("x")
    >>> Transpose(A + B) * A
    MatMul(Transpose(MatAdd(A, B)), A)
    >>> Determinant(A * B) + x
    Add(Determinant(MatMul(A, B)), x)
    >>> Determinant(x)
    Traceback (most recent call last):
        ...
    TypeError: Determinant expects MatrixKind(NumberKind), got NumberKind: x

Known gaps:

- A matrix has no shape. Every ``Matrix`` is of the same kind, so adding or
  multiplying matrices whose shapes do not match is not an error.
- The elements can only be numbers. ``MatrixKind`` can be given any kind,
  but the functions here are declared only for ``MatrixKind(NumberKind)``,
  and a matrix of any other kind has no functions and no operators.
- A number times a matrix has no function, so ``x * A`` and ``A * x`` are
  a ``TypeError``.
- There are no explicit matrices: nothing builds a matrix from its elements.
"""

from ._core import declare_kind_family, set_operator
from .domains import declare_function
from .kinds import NumberKind

__all__ = [
    "MatrixKind", "Matrix",
    "MatAdd", "MatMul", "Transpose", "Inverse", "Determinant", "Trace",
]

MatrixKind = declare_kind_family("MatrixKind", params=1)

Matrix = MatrixKind(NumberKind)

# No domain is stated (domain=None): a matrix has no shape yet, so neither
# matching shapes nor an invertible matrix for Inverse can be written.
MatAdd = declare_function("MatAdd", rest=Matrix, returns=Matrix, domain=None)
MatMul = declare_function("MatMul", rest=Matrix, returns=Matrix, domain=None)
Transpose = declare_function("Transpose", Matrix, returns=Matrix, domain=None)
Inverse = declare_function("Inverse", Matrix, returns=Matrix, domain=None)
Determinant = declare_function("Determinant", Matrix, returns=NumberKind, domain=None)
Trace = declare_function("Trace", Matrix, returns=NumberKind, domain=None)

# Which function each operator builds when the left operand is a Matrix.
set_operator(Matrix, "+", MatAdd)
set_operator(Matrix, "*", MatMul)
