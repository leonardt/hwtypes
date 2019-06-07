import pytest
import operator

import ctypes
import random
from hwtypes import FPVector, RoundingMode,BitVector
from hwtypes import z3FPVector
import math
import gmpy2
import z3

z3Float = z3FPVector[8, 23, RoundingMode.RNE, True]
Float = FPVector[8, 23, RoundingMode.RNE, True]

z3Double = z3FPVector[11, 52, RoundingMode.RNE, True]
Double = FPVector[11, 52, RoundingMode.RNE, True]

NTESTS = 16

@pytest.mark.parametrize("eb", [8, 11])
@pytest.mark.parametrize("mb", [7, 23, 52])
@pytest.mark.parametrize("mode", [
    RoundingMode.RNE,
    RoundingMode.RNA,
    RoundingMode.RTP,
    RoundingMode.RTN,
    RoundingMode.RTZ,
    ])
@pytest.mark.parametrize("ieee", [False, True])
def test_reinterpret_bv(eb, mb, mode, ieee):
    FT = z3FPVector[eb, mb, mode, ieee]
    ms = FT.mantissa_size
    for _ in range(NTESTS):
        bv1 = BitVector.random(FT.size)
        #dont generate denorms or NaN unless ieee compliant
        while ((not ieee)
                and (bv1[ms:-1] == 0 or bv1[ms:-1] == -1)
                and (bv1[:ms] != 0)):
            if bv1[ms:-1] == -1:
                assert (FT.reinterpret_from_bv(bv1).fp_is_infinite())._value
            else:
                assert (FT.reinterpret_from_bv(bv1).fp_is_zero())._value
            bv1 = BitVector.random(FT.size)

        f = FT.reinterpret_from_bv(bv1)
        bv2 = f.reinterpret_as_bv()
        if not bool(f.fp_is_NaN()._value):
            assert (bv2 == bv1)._value
        else:
            #exponents should be -1
            assert bv1[ms:-1] == BitVector[FT.exponent_size](-1)
            #mantissa should be non 0
            assert (bv1[:ms] != 0)._value

@pytest.mark.parametrize("eb", [8, 11])
@pytest.mark.parametrize("mb", [7, 23, 52])
@pytest.mark.parametrize("mode", [
    RoundingMode.RNE,
    RoundingMode.RNA,
    RoundingMode.RTP,
    RoundingMode.RTN,
    RoundingMode.RTZ,
    ])
@pytest.mark.parametrize("ieee", [
    False,
    True,
    ])
@pytest.mark.parametrize("mean, variance", [
    (0, 2**-64),
    (0, 2**-16),
    (0, 2**-4),
    (0, 1),
    (0, 2**4),
    (0, 2**16),
    (0, 2**64),
    ])
def test_reinterpret(eb, mb, mode, ieee, mean, variance):
    T = FPVector[eb, mb, mode, ieee]
    ZT = z3FPVector[eb, mb, mode, ieee]
    for _ in range(NTESTS):
        x = random.normalvariate(mean, variance)
        tx = T(x)
        zx = ZT.reinterpret_from_bv(tx.reinterpret_as_bv())
        assert (zx == tx)._value, (x, zx.reinterpret_as_bv(), tx.reinterpret_as_bv())
        assert (ZT.reinterpret_from_bv(zx.reinterpret_as_bv()) == zx)._value
        assert (zx.reinterpret_as_bv() == tx.reinterpret_as_bv())._value

@pytest.mark.parametrize("op", [operator.neg, operator.abs, lambda x : abs(x).fp_sqrt()])
@pytest.mark.parametrize("eb", [8, 11])
@pytest.mark.parametrize("mb", [7, 23, 52])
@pytest.mark.parametrize("mode", [
    RoundingMode.RNE,
    RoundingMode.RNA,
    RoundingMode.RTP,
    RoundingMode.RTN,
    RoundingMode.RTZ,
    ])
@pytest.mark.parametrize("ieee", [False, True])
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
        tx = T(x)
        zx = ZT.reinterpret_from_bv(tx.reinterpret_as_bv())
        assert (zx == tx)._value
        assert (zx == ZT.reinterpret_from_bv(tx.reinterpret_as_bv()))._value
        assert (zx.reinterpret_as_bv() == tx.reinterpret_as_bv())._value
        zr, tr = op(zx), op(tx)
        assert (zr == tr)._value
        assert (zr.reinterpret_as_bv() == tr.reinterpret_as_bv())._value
        assert (tr.reinterpret_as_bv() == BitVector[T.size](zr.reinterpret_as_bv()._value.as_long()))._value
@pytest.mark.parametrize("op", [operator.add, operator.sub, operator.mul, operator.truediv])
@pytest.mark.parametrize("eb", [8, 11])
@pytest.mark.parametrize("mb", [7, 23, 52])
@pytest.mark.parametrize("mode", [
    RoundingMode.RNE,
    #RoundingMode.RNA,
    RoundingMode.RTP,
    RoundingMode.RTN,
    RoundingMode.RTZ,
    ])
@pytest.mark.parametrize("ieee", [
    False,
    True,
    ])
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
        tx, ty = T(x), T(y)
        zx, zy = ZT.reinterpret_from_bv(tx.reinterpret_as_bv()), ZT.reinterpret_from_bv(ty.reinterpret_as_bv())
        zr, tr = op(zx, zy), op(tx, ty)
        assert (zr == tr)._value
        if tr.fp_is_zero():
            assert zr.fp_is_zero()._value
            assert (zr.reinterpret_as_bv()[:-1] == tr.reinterpret_as_bv()[:-1])._value
        else:
            assert (zr.reinterpret_as_bv() == tr.reinterpret_as_bv())._value
            assert (tr.reinterpret_as_bv() == BitVector[T.size](zr.reinterpret_as_bv()._value.as_long()))._value

@pytest.mark.parametrize("op", [operator.eq, operator.ne, operator.lt, operator.le, operator.gt, operator.ge])
@pytest.mark.parametrize("eb", [8, 11])
@pytest.mark.parametrize("mb", [7, 23, 52])
@pytest.mark.parametrize("mode", [
    RoundingMode.RNE,
    RoundingMode.RNA,
    RoundingMode.RTP,
    RoundingMode.RTN,
    RoundingMode.RTZ,
    ])
@pytest.mark.parametrize("ieee", [False, True])
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
        tx, ty = T(x), T(y)
        zx, zy = ZT.reinterpret_from_bv(tx.reinterpret_as_bv()), ZT.reinterpret_from_bv(ty.reinterpret_as_bv())
        zr, tr = op(zx, zy), op(tx, ty)
        assert (zr == tr)._value
