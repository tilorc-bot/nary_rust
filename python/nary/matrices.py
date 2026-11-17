"""Matrices of numbers, of the kind MatrixKind(NumberKind)."""

from ._core import function, set_operator
from .kinds import MatrixKind, NumberKind

_Matrix = MatrixKind(NumberKind)

# Matrix multiplication does not commute, so matrices have their own Add and
# Mul rather than sharing the ones for numbers.

MatAdd = function("MatAdd", rest=_Matrix, returns=_Matrix)
MatMul = function("MatMul", rest=_Matrix, returns=_Matrix)
Transpose = function("Transpose", _Matrix, returns=_Matrix)
Inverse = function("Inverse", _Matrix, returns=_Matrix)
Determinant = function("Determinant", _Matrix, returns=NumberKind)

# Which function each operator builds when the operand is a
# MatrixKind(NumberKind). Other matrix kinds have no operators.
set_operator(_Matrix, "+", MatAdd)
set_operator(_Matrix, "*", MatMul)

# TODO: a number times a matrix needs a function of its own. 2 * A and x * A
# are errors.
