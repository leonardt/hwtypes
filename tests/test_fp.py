import pytest
import operator

import ctypes
import random
from hwtypes import FPVector, RoundingMode,BitVector
import math
import gmpy2

#A sort of reference vector to test against
#Wraps either ctypes.c_float or ctypes.c_double
def _c_type_vector(T):
    class vector:
        def __init__(self, value):
            self._value = T(value)

        def __repr__(self):
            return f'{self.value}'

        @property
        def value(self) -> float:
            return self._value.value

        def fp_abs(self):
            if self.value < 0:
                return type(self)(-self.value)
            else:
                return type(self)(self.value)

        def fp_neg(self):
            return type(self)(-self.value)

        def fp_add(self, other):
            return type(self)(self.value + other.value)

        def fp_sub(self, other):
            return type(self)(self.value - other.value)

        def fp_mul(self, other):
            return type(self)(self.value * other.value)

        def fp_div(self, other):
            return type(self)(self.value / other.value)

        def fp_fma(self, coef, offset):
            raise NotImplementedError()

        def fp_sqrt(self):
            return type(self)(math.sqrt(self.value))

        def fp_rem(self, other):
            return type(self)(math.remainder(self.value))

        def fp_round_to_integral(self):
            return type(self)(math.round(self.value))

        def fp_min(self, other):
            return type(self)(min(self.value, other.value))

        def fp_max(self, other):
            return type(self)(max(self.value, other.value))

        def fp_leq(self, other):
            return self.value <= other.value

        def fp_lt(self, other):
            return self.value < other.value

        def fp_geq(self, other):
            return self.value >= other.value

        def fp_gt(self, other):
            return self.value > other.value

        def fp_eq(self, other):
            return self.value == other.value

        def fp_is_normal(self):
            raise NotImplementedError()

        def fp_is_subnormal(self):
            raise NotImplementedError()

        def fp_is_zero(self):
            return self.value == 0.0

        def fp_is_infinite(self):
            return math.isinf(self.value)

        def fp_is_NaN(self):
            return math.isnan(self.value)

        def fp_is_negative(self):
            return self.value < 0.0

        def fp_is_positive(self):
            return self.value > 0.0

        def to_ubv(self, size : int):
            raise NotImplementedError()

        def to_sbv(self, size : int):
            raise NotImplementedError()

        def reinterpret_as_bv(self):
            raise NotImplementedError()

        def __neg__(self): return self.fp_neg()
        def __abs__(self): return self.fp_abs()
        def __add__(self, other): return self.fp_add(other)
        def __sub__(self, other): return self.fp_sub(other)
        def __mul__(self, other): return self.fp_mul(other)
        def __truediv__(self, other): return self.fp_div(other)
        def __mod__(self, other): return self.fp_rem(other)

        def __eq__(self, other): return self.fp_eq(other)
        def __ne__(self, other): return ~(self.fp_eq(other))
        def __ge__(self, other): return self.fp_geq(other)
        def __gt__(self, other): return self.fp_gt(other)
        def __le__(self, other): return self.fp_leq(other)
        def __lt__(self, other): return self.fp_lt(other)

        def __float__(self):
            return self.value

    return vector

NTESTS = 128

@pytest.mark.parametrize("mode", [
    RoundingMode.RNE,
    RoundingMode.RNA,
    RoundingMode.RTP,
    RoundingMode.RTN,
    RoundingMode.RTZ,
    ])
@pytest.mark.parametrize("ieee", [False, True])
def test_init(mode, ieee):
    BigFloat = FPVector[27,100, mode, ieee]
    class F:
        def __float__(self):
            return 0.5

    class I:
        def __int__(self):
            return 1

    assert BigFloat(0.5) == BigFloat(F())
    assert BigFloat(1) == BigFloat(I())
    assert BigFloat(0.5) == BigFloat('0.5')
    assert BigFloat('1/3') == BigFloat(1)/BigFloat(3)
    assert BigFloat('1/3') != BigFloat(1/3) # as 1/3 is performed in python floats

@pytest.mark.parametrize("FT", [
    FPVector[8, 7, RoundingMode.RNE, True],
    FPVector[8, 7, RoundingMode.RNE, False],
    FPVector[11, 52, RoundingMode.RNE, True],
    FPVector[11, 52, RoundingMode.RNE, False],
    ])
@pytest.mark.parametrize("allow_inf", [False, True])
def test_random(FT, allow_inf):
    for _ in  range(NTESTS):
        r = FT.random(allow_inf)
        assert allow_inf or not r.fp_is_infinite()
        assert not r.fp_is_NaN()

@pytest.mark.parametrize("FT", [
    FPVector[8, 7, RoundingMode.RNE, True],
    FPVector[8, 7, RoundingMode.RNE, False],
    FPVector[11, 52, RoundingMode.RNE, True],
    FPVector[11, 52, RoundingMode.RNE, False],
    ])
def test_reinterpret(FT):
    #basic sanity
    for x in ('-2.0', '-1.75', '-1.5', '-1.25',
              '-1.0', '-0.75', '-0.5', '-0.25',
               '0.0',  '0.25',  '0.5',  '0.75',
               '1.0',  '1.25',  '1.5',  '1.75',):
        f1 = FT(x)
        bv = f1.reinterpret_as_bv()
        f2 = FT.reinterpret_from_bv(bv)
        assert f1 == f2

    #epsilon
    f1 = FT(1)
    while f1/2 != 0:
        bv = f1.reinterpret_as_bv()
        f2 = FT.reinterpret_from_bv(bv)
        assert f1 == f2
        f1 = f1/2

    #using FPVector.random
    for _ in range(NTESTS):
        f1 = FT.random()
        bv = f1.reinterpret_as_bv()
        f2 = FT.reinterpret_from_bv(bv)
        assert f1 == f2

@pytest.mark.parametrize("FT", [
    FPVector[8, 23, RoundingMode.RNE, True],
    FPVector[8, 23, RoundingMode.RNE, False],
    FPVector[11, 52, RoundingMode.RNE, True],
    FPVector[11, 52, RoundingMode.RNE, False],
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
def test_reinterpret_pyrandom(FT, mean, variance):
    for _ in range(NTESTS):
        x = random.normalvariate(mean, variance)
        f1 = FT(x)
        bv = f1.reinterpret_as_bv()
        f2 = FT.reinterpret_from_bv(bv)
        assert f1 == f2

@pytest.mark.parametrize("FT", [
    FPVector[8, 7, RoundingMode.RNE, True],
    FPVector[8, 7, RoundingMode.RNE, False],
    FPVector[11, 52, RoundingMode.RNE, True],
    FPVector[11, 52, RoundingMode.RNE, False],
    ])
def test_reinterpret_bv(FT):
    ms = FT.mantissa_size
    for _ in range(NTESTS):
        bv1 = BitVector.random(FT.size)
        #dont generate denorms or NaN unless ieee compliant
        while (not FT.ieee_compliance
                and (bv1[ms:-1] == 0 or bv1[ms:-1] == -1)
                and bv1[:ms] != 0):
            bv1 = BitVector.random(FT.size)

        f = FT.reinterpret_from_bv(bv1)
        bv2 = f.reinterpret_as_bv()
        if not f.fp_is_NaN():
            assert bv1 == bv2
        else:
            #exponents should be -1
            assert bv1[ms:-1] == BitVector[FT.exponent_size](-1)
            assert bv2[ms:-1] == BitVector[FT.exponent_size](-1)
            #mantissa should be non 0
            assert bv1[:ms] != 0
            assert bv2[:ms] != 0

def test_reinterpret_bv_corner():
    for _ in range(NTESTS):
        FT = FPVector[random.randint(3, 16),
                      random.randint(2, 64),
                      random.choice(list(RoundingMode)),
                      True]
        bv_pinf = BitVector[FT.mantissa_size](0).concat(BitVector[FT.exponent_size](-1)).concat(BitVector[1](0))
        bv_ninf = BitVector[FT.mantissa_size](0).concat(BitVector[FT.exponent_size](-1)).concat(BitVector[1](1))
        pinf = FT.reinterpret_from_bv(bv_pinf)
        ninf = FT.reinterpret_from_bv(bv_ninf)
        assert pinf.reinterpret_as_bv() == bv_pinf
        assert ninf.reinterpret_as_bv() == bv_ninf
        assert pinf.fp_is_positive()
        assert pinf.fp_is_infinite()
        assert ninf.fp_is_negative()
        assert ninf.fp_is_infinite()

        bv_pz = BitVector[FT.size](0)
        bv_nz = BitVector[FT.size-1](0).concat(BitVector[1](1))
        pz = FT.reinterpret_from_bv(bv_pz)
        nz = FT.reinterpret_from_bv(bv_nz)
        assert pz.reinterpret_as_bv() == bv_pz
        assert nz.reinterpret_as_bv() == bv_nz
        assert pz.fp_is_zero()
        assert nz.fp_is_zero()

        bv_nan = BitVector[FT.mantissa_size](1).concat(BitVector[FT.exponent_size](-1)).concat(BitVector[1](0))
        nan = FT.reinterpret_from_bv(bv_nan)
        assert nan.reinterpret_as_bv() == bv_nan
        assert nan.fp_is_NaN()

@pytest.mark.parametrize("CT, FT", [
    (_c_type_vector(ctypes.c_float), FPVector[8, 23, RoundingMode.RNE, True]),
    (_c_type_vector(ctypes.c_double), FPVector[11, 52, RoundingMode.RNE, True]),])
def test_epsilon(CT, FT):
    cx, fx = CT(1), FT(1)
    c2, f2 = CT(2), FT(2)
    while not ((cx/c2).fp_is_zero() or (fx/f2).fp_is_zero()):
        assert float(cx) == float(fx)
        cx = cx/c2
        fx = fx/f2

    assert not cx.fp_is_zero()
    assert not fx.fp_is_zero()
    assert (cx/c2).fp_is_zero()
    assert (fx/f2).fp_is_zero()

@pytest.mark.parametrize("op", [operator.neg, operator.abs, lambda x : abs(x).fp_sqrt()])
@pytest.mark.parametrize("CT, FT", [
    (_c_type_vector(ctypes.c_float), FPVector[8, 23, RoundingMode.RNE, True]),
    (_c_type_vector(ctypes.c_double), FPVector[11, 52, RoundingMode.RNE, True]),])
@pytest.mark.parametrize("mean, variance", [
    (0, 2**-64),
    (0, 2**-16),
    (0, 2**-4),
    (0, 1),
    (0, 2**4),
    (0, 2**16),
    (0, 2**64),
    ])
def test_unary_op(op, CT, FT, mean, variance):
    for _ in range(NTESTS):
        x = random.normalvariate(mean, variance)
        cx = CT(x)
        fx = FT(x)
        assert float(cx) == float(fx)
        cr, fr = op(cx), op(fx)
        assert float(cr) == float(fr)

@pytest.mark.parametrize("op", [operator.add, operator.sub, operator.mul, operator.truediv])
@pytest.mark.parametrize("CT, FT", [
    (_c_type_vector(ctypes.c_float), FPVector[8, 23, RoundingMode.RNE, True]),
    (_c_type_vector(ctypes.c_double), FPVector[11, 52, RoundingMode.RNE, True]),])
@pytest.mark.parametrize("mean, variance", [
    (0, 2**-64),
    (0, 2**-16),
    (0, 2**-4),
    (0, 1),
    (0, 2**4),
    (0, 2**16),
    (0, 2**64),
    ])
def test_bin_op(op, CT, FT, mean, variance):
    for _ in range(NTESTS):
        x = random.normalvariate(mean, variance)
        y = random.normalvariate(mean, variance)
        cx, cy = CT(x), CT(y)
        fx, fy = FT(x), FT(y)
        cr, fr = op(cx, cy), op(fx, fy)
        assert float(cr) == float(fr)

@pytest.mark.parametrize("op", [operator.eq, operator.ne, operator.lt, operator.le, operator.gt, operator.ge])
@pytest.mark.parametrize("CT, FT", [
    (_c_type_vector(ctypes.c_float), FPVector[8, 23, RoundingMode.RNE, True]),
    (_c_type_vector(ctypes.c_double), FPVector[11, 52, RoundingMode.RNE, True]),])
@pytest.mark.parametrize("mean, variance", [
    (0, 2**-64),
    (0, 2**-16),
    (0, 2**-4),
    (0, 1),
    (0, 2**4),
    (0, 2**16),
    (0, 2**64),
    ])
def test_bool_op(op, CT, FT, mean, variance):
    for _ in range(NTESTS):
        x = random.normalvariate(mean, variance)
        y = random.normalvariate(mean, variance)
        cx, cy = CT(x), CT(y)
        fx, fy = FT(x), FT(y)
        cr, fr = op(cx, cy), op(fx, fy)
        assert bool(cr) == bool(fr)
