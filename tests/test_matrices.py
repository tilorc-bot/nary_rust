"""Matrices of numbers, declared in nary.matrices."""

import pytest
from nary import NumberKind
from nary.matrices import (
    Determinant, Inverse, MatAdd, MatMul, Matrix, MatrixKind, Trace, Transpose,
)

A, B = Matrix("A"), Matrix("B")
x, y = NumberKind("x"), NumberKind("y")


def test_each_function_and_its_result_kind():
    assert Matrix is MatrixKind(NumberKind)
    for expr, text, result in (
        (MatAdd(A, B, A), "MatAdd(A, B, A)", Matrix),
        (MatMul(A, B), "MatMul(A, B)", Matrix),
        (Transpose(A), "Transpose(A)", Matrix),
        (Inverse(A), "Inverse(A)", Matrix),
        (Determinant(A), "Determinant(A)", NumberKind),
        (Trace(A), "Trace(A)", NumberKind),
    ):
        assert repr(expr) == text
        assert expr.kind is result


def test_operators_build_matrix_functions_for_matrices_only():
    assert A + B == MatAdd(A, B)
    assert A * B == MatMul(A, B)
    assert (A * B).kind is Matrix
    assert repr(Trace(A * B) + x * y) == "Add(Trace(MatMul(A, B)), Mul(x, y))"


def test_a_number_is_not_a_matrix():
    with pytest.raises(TypeError, match=r"^Inverse expects MatrixKind\(NumberKind\), got NumberKind: x$"):
        Inverse(x)
    with pytest.raises(TypeError, match=r"^Mul expects NumberKind, got MatrixKind\(NumberKind\): A$"):
        x * A
