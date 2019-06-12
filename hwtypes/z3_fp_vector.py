from .bit_vector_abc import AbstractBitVector
from .fp_vector_abc import AbstractFPVector, RoundingMode
from .fp_vector import FPVector
from .z3_bit_vector import z3BitVector, z3Bit
import z3

import typing as tp
import itertools as it
import functools as ft

import re
import warnings
import weakref

import random

__ALL__ = ['z3FPVector']

class _SMYBOLIC:
    def __repr__(self):
        return 'SYMBOLIC'

class _AUTOMATIC:
    def __repr__(self):
        return 'AUTOMATIC'

SMYBOLIC = _SMYBOLIC()
AUTOMATIC = _AUTOMATIC()

_var_counter = it.count()
_name_table = weakref.WeakValueDictionary()
_free_names = []

def _gen_name():
    if _free_names:
        return _free_names.pop()
    name = f'FP_{next(_var_counter)}'
    while name in _name_table:
        name = f'FP_{next(_var_counter)}'
    return name

_name_re = re.compile(r'FP_\d+')

_mode_2_z3 = {
    RoundingMode.RNE : z3.RoundNearestTiesToEven(),
    RoundingMode.RNA : z3.RoundNearestTiesToAway(),
    RoundingMode.RTP : z3.RoundTowardPositive(),
    RoundingMode.RTN : z3.RoundTowardNegative(),
    RoundingMode.RTZ : z3.RoundTowardZero(),
}

def _coerce(T : tp.Type['z3FPVector'], val : tp.Any) -> 'FPVector':
    if not isinstance(val, T):
        return T(val)
    elif type(val).binding != T.binding:
        raise TypeError('Inconsistent FP type')
    else:
        return val

def fp_cast(fn : tp.Callable[['z3FPVector', 'z3FPVector'], tp.Any]) -> tp.Callable[['z3FPVector', tp.Any], tp.Any]:
    @ft.wraps(fn)
    def wrapped(self : 'z3FPVector', other : tp.Any) -> tp.Any:
        other = _coerce(type(self), other)
        return fn(self, other)
    return wrapped

class z3FPVector(AbstractFPVector):
    @classmethod
    def _get_sort(cls):
        return z3.FPSort(cls.exponent_size, cls.mantissa_size+1)

    @classmethod
    def _get_mode(cls):
        return _mode_2_z3[cls.mode]

    def __init__(self, value=SMYBOLIC, *, name=AUTOMATIC):
        cls = type(self)

        if name is not AUTOMATIC and value is not SMYBOLIC:
            raise TypeError('Can only name symbolic variables')
        elif name is not AUTOMATIC:
            if not isinstance(name, str):
                raise TypeError('Name must be string')
            elif name in _name_table:
                raise ValueError(f'Name {name} already in use')
            elif _name_re.fullmatch(name):
                warnings.warn('Name looks like an auto generated name, this might break things')
            _name_table[name] = self
        elif name is AUTOMATIC and value is SMYBOLIC:
            name = _gen_name()
            _name_table[name] = self

        sort = cls._get_sort()
        mode = cls._get_mode()

        if isinstance(value, z3.ExprRef):
            value = z3.simplify(value)

        if value is SMYBOLIC:
            value = z3.FP(name, sort)
        elif isinstance(value, z3.FPRef):
            if value.sort() != sort:
                raise TypeError('Inconsistent FP type')
            value = value
        elif isinstance(value, z3FPVector):
            if cls.binding != type(value).binding:
                raise TypeError('Inconsistent FP type')
            elif name is not AUTOMATIC and name != value.name:
                warnings.warn('Changing the name of a z3FPVector does not cause a new underlying smt variable to be created')
            value = value._value
        elif isinstance(value, FPVector):
            value = cls.reinterpret_from_bv(value.reinterpret_as_bv())._value
        elif isinstance(value, (float, str)):
            value = z3.fpRealToFP(mode, z3.RealVal(value), sort)
        elif hasattr(value, '__float__'):
            value = z3.fpRealToFP(mode, z3.RealVal(float(value)), sort)
        else:
            raise TypeError("Can't coerce {} to z3FPVector".format(type(value)))

        if not cls.ieee_compliance:
            value = z3.If(
                        z3.fpIsSubnormal(value),
                        z3.If(
                            z3.fpIsNegative(value),
                            z3.fpMinusZero(sort),
                            z3.fpPlusZero(sort)
                        ),
                        z3.If(
                            z3.fpIsNaN(value),
                            z3.fpPlusInfinity(sort),
                            value
                        )
                    )

        value = z3.simplify(value)

        self._name = name
        self._value = value

    def fp_abs(self) -> 'z3FPVector':
        return type(self)(z3.fpAbs(self._value))

    def fp_neg(self) -> 'z3FPVector':
        return type(self)(z3.fpNeg(self._value))

    @fp_cast
    def fp_add(self, other: 'z3FPVector') -> 'z3FPVector':
        return type(self)(z3.fpAdd(self._get_mode(), self._value, other._value))

    @fp_cast
    def fp_sub(self, other: 'z3FPVector') -> 'z3FPVector':
        return type(self)(z3.fpSub(self._get_mode(), self._value, other._value))

    @fp_cast
    def fp_mul(self, other: 'z3FPVector') -> 'z3FPVector':
        return type(self)(z3.fpMul(self._get_mode(), self._value, other._value))

    @fp_cast
    def fp_div(self, other: 'z3FPVector') -> 'z3FPVector':
        return type(self)(z3.fpDiv(self._get_mode(), self._value, other._value))

    def fp_fma(self, coef: 'z3FPVector', offset: 'z3FPVector') -> 'z3FPVector':
        cls = type(self)
        coef = _coerce(cls, coef)
        offset = _coerce(cls, offset)
        return cls(z3.fpFMA(self._get_mode(), self._value, coef._value, other._value))

    def fp_sqrt(self) -> 'z3FPVector':
        return type(self)(z3.fpSqrt(self._get_mode(), self._value))

    @fp_cast
    def fp_rem(self, other: 'z3FPVector') -> 'z3FPVector':
        return type(self)(z3.fpRem(self._get_mode(), self._value, other._value))


    def fp_round_to_integral(self) -> 'z3FPVector':
        return type(self)(z3.fpRoundToIntegral(self._get_mode(), self._value))

    @fp_cast
    def fp_min(self, other: 'z3FPVector') -> 'z3FPVector':
        return type(self)(z3.fpMin(self._value, other._value))

    @fp_cast
    def fp_max(self, other: 'z3FPVector') -> 'z3FPVector':
        return type(self)(z3.fpMax(self._value, other._value))

    @fp_cast
    def fp_leq(self, other: 'z3FPVector') ->  z3Bit:
        return z3Bit(z3.fpLEQ(self._value, other._value))

    @fp_cast
    def fp_lt(self, other: 'z3FPVector') ->  z3Bit:
        return z3Bit(z3.fpLT(self._value, other._value))

    @fp_cast
    def fp_geq(self, other: 'z3FPVector') ->  z3Bit:
        return z3Bit(z3.fpGEQ(self._value, other._value))

    @fp_cast
    def fp_gt(self, other: 'z3FPVector') ->  z3Bit:
        return z3Bit(z3.fpGT(self._value, other._value))

    @fp_cast
    def fp_eq(self, other: 'z3FPVector') ->  z3Bit:
        return z3Bit(z3.fpEQ(self._value, other._value))

    def fp_is_normal(self) -> z3Bit:
        return z3Bit(z3.fpIsNormal(self._value))

    def fp_is_subnormal(self) -> z3Bit:
        return z3Bit(z3.fpIsSubnormal(self._value))

    def fp_is_zero(self) -> z3Bit:
        return z3Bit(z3.fpIsZero(self._value))

    def fp_is_infinite(self) -> z3Bit:
        return z3Bit(z3.fpIsInf(self._value))

    def fp_is_NaN(self) -> z3Bit:
        return z3Bit(z3.fpIsNaN(self._value))

    def fp_is_negative(self) -> z3Bit:
        return z3Bit(z3.fpIsNegative(self._value))

    def fp_is_positive(self) -> z3Bit:
        return z3Bit(z3.fpIsPositive(self._value))

    def to_ubv(self, size : int) -> z3BitVector:
        return z3BitVector(z3.fpToUBV(self._get_mode(), self._value, z3.BitVecSort(size)))

    def to_sbv(self, size : int) -> z3BitVector:
        return z3BitVector(z3.fpToSBV(self._get_mode(), self._value, z3.BitVecSort(size)))

    def reinterpret_as_bv(self) -> z3BitVector:
        return z3BitVector[type(self).size](z3.fpToIEEEBV(self._value))

    @classmethod
    def reinterpret_from_bv(cls, value: AbstractBitVector) -> 'z3FPVector':
        #value = z3BitVector[value.size](value)
        #mantissa = value[:cls.mantissa_size]
        #exp      = value[cls.mantissa_size:-1]
        #sign     = value[-1:]
        #return cls(z3.fpFP(sign._value,exp._value,mantissa._value))
        return cls(z3.fpBVToFP(z3BitVector[cls.size](value)._value, cls._get_sort()))

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

    def __repr__(self):
        return f'{type(self)}({self._value.as_string()})'

