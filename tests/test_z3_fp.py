import pytest
import operator

import ctypes
import random
from hwtypes import FPVector, RoundingMode,BitVector
from hwtypes import z3FPVector
import math
import gmpy2

z3Float = z3FPVector[8, 23, RoundingMode.RNE, True]
Float = FPVector[8, 23, RoundingMode.RNE, True]

z3Double = z3FPVector[11, 52, RoundingMode.RNE, True]
Double = FPVector[11, 52, RoundingMode.RNE, True]

NTESTS = 100


@pytest.mark.parametrize("op", [operator.neg, operator.abs, lambda x : abs(x).fp_sqrt()])
@pytest.mark.parametrize("ZT, T", [
    (z3Float, Float),
    (z3Double, Double),])
@pytest.mark.parametrize("mean, variance", [
    (0, 2**-64),
    (0, 2**-16),
    (0, 2**-4),
    (0, 1),
    (0, 2**4),
    (0, 2**16),
    (0, 2**64),
    ])
def test_unary_op(op, ZT, T, mean, variance):
    for _ in range(NTESTS):
        x = random.normalvariate(mean, variance)
        zx = ZT(x)
        tx = T(x)
        assert zx == ZT.reinterpret_from_bv(tx.reinterpret_as_bv())
        zr, tr = op(zx), op(tx)
        assert zx == ZT.reinterpret_from_bv(tr.reinterpret_as_bv())

@pytest.mark.parametrize("op", [operator.add, operator.sub, operator.mul, operator.truediv])
@pytest.mark.parametrize("ZT, T", [
    (z3Float, Float),
    (z3Double, Double),])
@pytest.mark.parametrize("mean, variance", [
    (0, 2**-64),
    (0, 2**-16),
    (0, 2**-4),
    (0, 1),
    (0, 2**4),
    (0, 2**16),
    (0, 2**64),
    ])
def test_bin_op(op, ZT, T, mean, variance):
    for _ in range(NTESTS):
        x = random.normalvariate(mean, variance)
        y = random.normalvariate(mean, variance)
        zx, zy = ZT(x), ZT(y)
        tx, ty = T(x), T(y)
        zr, tr = op(zx, zy), op(tx, ty)
        assert zr == ZT.reinterpret_from_bv(tr.reinterpret_as_bv())

@pytest.mark.parametrize("op", [operator.eq, operator.ne, operator.lt, operator.le, operator.gt, operator.ge])
@pytest.mark.parametrize("ZT, T", [
    (z3Float, Float),
    (z3Double, Double),])
@pytest.mark.parametrize("mean, variance", [
    (0, 2**-64),
    (0, 2**-16),
    (0, 2**-4),
    (0, 1),
    (0, 2**4),
    (0, 2**16),
    (0, 2**64),
    ])
def test_bool_op(op, ZT, T, mean, variance):
    for _ in range(NTESTS):
        x = random.normalvariate(mean, variance)
        y = random.normalvariate(mean, variance)
        zx, zy = ZT(x), ZT(y)
        tx, ty = T(x), T(y)
        zr, tr = op(zx, zy), op(tx, ty)
        assert zr == tr
