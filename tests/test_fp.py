import pytest
import operator

import ctypes
import random
from hwtypes import FPVector, RoundingMode
import math

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

NTESTS = 100

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

@pytest.mark.parametrize("op", [operator.neg, operator.abs])
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
