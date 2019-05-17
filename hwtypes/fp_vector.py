import typing as tp
import functools
import gmpy2

from .fp_vector_abc import AbstractFPVector, RoundingMode
from .bit_vector import Bit, BitVector, SIntVector

_mode_2_gmpy2 = {
    RoundingMode.RNE : gmpy2.RoundToNearest,
    RoundingMode.RNA : gmpy2.RoundAwayZero,
    RoundingMode.RTP : gmpy2.RoundUp,
    RoundingMode.RTN : gmpy2.RoundDown,
    RoundingMode.RTZ : gmpy2.RoundToZero,
}

def _coerce(T : tp.Type['FPVector'], val : tp.Any) -> 'FPVector':
    if not isinstance(val, FPVector):
        return T(val)
    elif type(val).info != T.info:
        raise TypeError('Inconsistent FP type')
    else:
        return val

def fp_cast(fn : tp.Callable[['FPVector', 'FPVector'], tp.Any]) -> tp.Callable[['FPVector', tp.Any], tp.Any]:
    @functools.wraps(fn)
    def wrapped(self : 'FPVector', other : tp.Any) -> tp.Any:
        other = _coerce(type(self), other)
        return fn(self, other)
    return wrapped

def set_context(fn: tp.Callable) -> tp.Callable:
    @functools.wraps(fn)
    def wrapped(self : 'FPVector', *args, **kwargs):
        with gmpy2.local_context(self._ctx):
            return fn(self, *args, **kwargs)
    return wrapped

class FPVector(AbstractFPVector):
    def __init__(self, value):
        cls = type(self)
        if cls.ieee_compliance:
            precision=cls.mantissa_size+1
            emax=1<<(cls.exponent_size - 1)
            emin=4-emax-precision
            subnormalize=True
        else:
            precision=cls.mantissa_size+1
            emax=1<<(cls.exponent_size - 1)
            emin=3-emax
            subnormalize=False

        self._ctx = ctx = gmpy2.context(
                precision=precision,
                emin=emin,
                emax=emax,
                round=_mode_2_gmpy2[cls.mode],
                subnormalize=cls.ieee_compliance,
                allow_complex=False,
        )


        with gmpy2.local_context(ctx):
            value = gmpy2.mpfr(value)
            if gmpy2.is_nan(value) and not cls.ieee_compliance:
                if gmpy2.is_signed(value):
                    self._value = gmpy2.mpfr('-0')
                else:
                    self._value = gmpy2.mpfr('0')

            else:
                self._value = value

    def __repr__(self):
        return f'{self._value}'

    @set_context
    def fp_abs(self) -> 'FPVector':
        v = self._value
        return type(self)(v if v >= 0 else -v)

    @set_context
    def fp_neg(self) -> 'FPVector':
        return type(self)(-self._value)

    @set_context
    @fp_cast
    def fp_add(self, other : 'FPVector') -> 'FPVector':
        return type(self)(self._value + other._value)

    @set_context
    @fp_cast
    def fp_sub(self, other : 'FPVector') -> 'FPVector':
        return type(self)(self._value - other._value)

    @set_context
    @fp_cast
    def fp_mul(self, other : 'FPVector') -> 'FPVector':
        return type(self)(self._value * other._value)

    @set_context
    @fp_cast
    def fp_div(self, other : 'FPVector') -> 'FPVector':
        return type(self)(self._value / other._value)

    @set_context
    def fp_fma(self, coef, offset) -> 'FPVector':
        cls = type(self)
        coef = _coerce(cls, coef)
        offset = _coerce(cls, offset)
        return cls(gmpy2.fma(self._value, coef._value, offset._value))

    @set_context
    def fp_sqrt(self) -> 'FPVector':
        return type(self)(gmpy2.sqrt(self._value))

    @set_context
    @fp_cast
    def fp_rem(self, other : 'FPVector') -> 'FPVector':
        return type(self)(gmpy2.remainder(self._value, other._value))

    @set_context
    def fp_round_to_integral(self) -> 'FPVector':
        return type(self)(gmpy2.rint(self._value))

    @set_context
    @fp_cast
    def fp_min(self, other : 'FPVector') -> 'FPVector':
        return type(self)(gmpy2.minnum(self._value, other._value))

    @set_context
    @fp_cast
    def fp_max(self, other : 'FPVector') -> 'FPVector':
        return type(self)(gmpy2.maxnum(self._value, other._value))

    @set_context
    @fp_cast
    def fp_leq(self, other : 'FPVector') -> Bit:
        return Bit(self._value <= other._value)

    @set_context
    @fp_cast
    def fp_lt(self, other : 'FPVector') ->  Bit:
        return Bit(self._value < other._value)

    @set_context
    @fp_cast
    def fp_geq(self, other : 'FPVector') ->  Bit:
        return Bit(self._value >= other._value)

    @set_context
    @fp_cast
    def fp_gt(self, other : 'FPVector') ->  Bit:
        return Bit(self._value > other._value)

    @set_context
    @fp_cast
    def fp_eq(self, other : 'FPVector') ->  Bit:
        return Bit(self._value == other._value)

    @set_context
    def fp_is_normal(self) -> Bit:
        if not type(self).ieee_compliance:
            return Bit(True)
        else:
            raise NotImplementedError()

    @set_context
    def fp_is_subnormal(self) -> Bit:
        if not type(self).ieee_compliance:
            return Bit(False)
        else:
            raise NotImplementedError()

    @set_context
    def fp_is_zero(self) -> Bit:
        return Bit(gmpy2.is_zero(self._value))

    @set_context
    def fp_is_infinite(self) -> Bit:
        return Bit(gmpy2.is_infinite(self._value))

    @set_context
    def fp_is_NaN(self) -> Bit:
        return Bit(gmpy2.is_nan(self._value))

    @set_context
    def fp_is_negative(self) -> Bit:
        return Bit(self._value < 0)

    @set_context
    def fp_is_positive(self) -> Bit:
        return Bit(self._value > 0)

    @set_context
    def to_ubv(self, size : int) -> BitVector:
        return BitVector[size](int(self._value))

    @set_context
    def to_sbv(self, size : int) -> SIntVector:
        return SIntVector[size](int(self._value))

    @set_context
    def reinterpret_as_bv(self) -> BitVector:
        cls = type(self)
        bias = (1 << (cls.exponent_size - 1)) - 1

        sign_bit = BitVector[1](gmpy2.is_signed(self._value))
        v = self._value

        mantissa_int, exp =  v.as_mantissa_exp()
        exp = exp + cls.mantissa_size
        if mantissa_int == 0:
            return BitVector.concat(sign_bit, BitVector[cls.size-1](0))


        if exp < 1-bias:
            #denorm
            assert cls.ieee_compliance
            raise NotImplementedError()
        else:
            exp = exp + bias
            assert exp.bit_length() <= cls.exponent_size
            if sign_bit:
                mantissa = -BitVector[cls.mantissa_size+1](mantissa_int)
            else:
                mantissa = BitVector[cls.mantissa_size+1](mantissa_int)
            mantissa_bits = mantissa[:cls.mantissa_size]
            exp_bits = BitVector[cls.exponent_size](exp)
            return BitVector.concat(BitVector.concat(sign_bit, exp_bits), mantissa_bits)


    @classmethod
    def reinterpret_from_bv(cls, value: BitVector) -> 'FPVector':
        if cls.size != value.size:
            raise TypeError()

        mantissa = value[:cls.mantissa_size]
        exp      = value[cls.mantissa_size:-1]
        sign     = value[-1]
        assert exp.size == cls.exponent_size

        if exp == 0:
            if mantissa != 0:
                #denorm
                assert cls.ieee_compliance
                raise NotImplementedError()
            elif sign:
                return cls('-0')
            else:
                return cls('0')
        elif exp == -1:
            if mantissa == 0:
                if sign:
                    return cls('-inf')
                else:
                    return cls('inf')
            else:
                return cls('nan')
        else:
            #unbias the exponent
            bias = (1 << (cls.exponent_size - 1)) - 1
            exp = exp - bias

            s = ['-1.' if sign else '1.', mantissa.binary_string()]
            s.append('e')
            s.append(str(exp.as_sint()))
            return cls(gmpy2.mpfr(''.join(s),cls.mantissa_size+1, 2))


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

    @set_context
    def __float__(self):
        return float(self._value)
