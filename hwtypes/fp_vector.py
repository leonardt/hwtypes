import functools
import gmpy2
import random
import typing as tp
import warnings

from .bit_vector import Bit, BitVector, SIntVector
from .fp_vector_abc import AbstractFPVector, RoundingMode

__ALL__ = ['FPVector']

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
    elif type(val).binding != T.binding:
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
        with gmpy2.local_context(self._ctx_):
            return fn(self, *args, **kwargs)
    return wrapped

class FPVector(AbstractFPVector):
    @set_context
    def __init__(self, value):
        # Because for some reason gmpy2.mpfr is a function and not a type
        if isinstance(value, type(gmpy2.mpfr(0))):
            #need to specify precision because mpfr will use the input
            #precision not the context precision when constructing from mpfr
            value = gmpy2.mpfr(value, self._ctx_.precision)
        elif isinstance(value, FPVector):
            value = gmpy2.mpfr(value._value, self._ctx_.precision)
        elif isinstance(value, (int, float, type(gmpy2.mpz(0)), type(gmpy2.mpq(0)))):
            value = gmpy2.mpfr(value)
        elif isinstance(value, str):
            try:
                #Handles '0.5'
                value = gmpy2.mpfr(value)
            except ValueError:
                try:
                    #Handles '1/2'
                    value = gmpy2.mpfr(gmpy2.mpq(value))
                except ValueError:
                    raise ValueError('Invalid string')
        elif hasattr(value, '__float__'):
            value = gmpy2.mpfr(float(value))
        elif hasattr(value, '__int__'):
            value = gmpy2.mpfr(int(value))
        else:
            try:
                #if gmpy2 doesn't complain I wont
                value = gmpy2.mpfr(value)
            except TypeError:
                raise TypeError(f"Can't construct FPVector from {type(value)}")

        if gmpy2.is_nan(value) and not type(self).ieee_compliance:
            if gmpy2.is_signed(value):
                self._value = gmpy2.mpfr('-inf')
            else:
                self._value = gmpy2.mpfr('inf')

        else:
            self._value = value

    @classmethod
    def __init_subclass__(cls, **kwargs):
        if cls.is_bound:
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

            ctx = gmpy2.context(
                    precision=precision,
                    emin=emin,
                    emax=emax,
                    round=_mode_2_gmpy2[cls.mode],
                    subnormalize=cls.ieee_compliance,
                    allow_complex=False,
            )

            if hasattr(cls, '_ctx_'):
                c_ctx = cls._ctx_
                if not isinstance(c_ctx, type(ctx)):
                    raise TypeError('class attribute _ctx_ is reversed by FPVector')
                #stupid compare because contexts aren't comparable
                elif (c_ctx.precision != ctx.precision
                        or c_ctx.real_prec != ctx.real_prec
                        or c_ctx.imag_prec != ctx.imag_prec
                        or c_ctx.round != ctx.round
                        or c_ctx.real_round != ctx.real_round
                        or c_ctx.imag_round != ctx.imag_round
                        or c_ctx.emax != ctx.emax
                        or c_ctx.emin != ctx.emin
                        or c_ctx.subnormalize != ctx.subnormalize
                        or c_ctx.trap_underflow != ctx.trap_underflow
                        or c_ctx.trap_overflow != ctx.trap_overflow
                        or c_ctx.trap_inexact != ctx.trap_inexact
                        or c_ctx.trap_erange != ctx.trap_erange
                        or c_ctx.trap_divzero != ctx.trap_divzero
                        or c_ctx.trap_expbound != ctx.trap_expbound
                        or c_ctx.allow_complex != ctx.allow_complex):
                    # this basically should never happen unless some one does
                    # class Foo(FPVector):
                    #   _ctx_ = gmpy2.context(....)
                    raise TypeError('Incompatible context types')

            cls._ctx_ = ctx



    def __repr__(self):
        return f'{type(self)}({self._value})'

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
        return ~(self.fp_is_zero() | self.fp_is_infinite() | self.fp_is_subnormal() | self.fp_is_NaN())

    @set_context
    def fp_is_subnormal(self) -> Bit:
        bv = self.reinterpret_as_bv()
        if (bv[type(self).mantissa_size:-1] == 0) & ~self.fp_is_zero():
            assert type(self).ieee_compliance
            return Bit(True)
        else:
            return Bit(False)


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
        sign_bit = BitVector[1](gmpy2.is_signed(self._value))

        if self.fp_is_zero():
            return BitVector[cls.size-1](0).concat(sign_bit)
        elif self.fp_is_infinite():
            exp_bits = BitVector[cls.exponent_size](-1)
            mantissa_bits = BitVector[cls.mantissa_size](0)
            return mantissa_bits.concat(exp_bits).concat(sign_bit)
        elif self.fp_is_NaN():
            exp_bits = BitVector[cls.exponent_size](-1)
            mantissa_bits = BitVector[cls.mantissa_size](1)
            return mantissa_bits.concat(exp_bits).concat(sign_bit)


        bias = (1 << (cls.exponent_size - 1)) - 1
        v = self._value

        mantissa_int, exp =  v.as_mantissa_exp()

        exp = exp + cls.mantissa_size

        if exp < 1-bias:
            if not cls.ieee_compliance:
                warnings.warn('denorm will be flushed to 0')
                mantissa_int = 0
            else:
                while exp < 1 - bias:
                    mantissa_int >>= 1
                    exp += 1
            exp = 0
        else:
            exp = exp + bias

        assert exp.bit_length() <= cls.exponent_size

        if sign_bit:
            mantissa = -BitVector[cls.mantissa_size+1](mantissa_int)
        else:
            mantissa = BitVector[cls.mantissa_size+1](mantissa_int)
        exp_bits = BitVector[cls.exponent_size](exp)
        mantissa_bits = mantissa[:cls.mantissa_size]
        return mantissa_bits.concat(exp_bits).concat(sign_bit)

    @classmethod
    @set_context
    def reinterpret_from_bv(cls, value: BitVector) -> 'FPVector':
        if cls.size != value.size:
            raise TypeError()

        mantissa = value[:cls.mantissa_size]
        exp      = value[cls.mantissa_size:-1]
        sign     = value[-1:]
        assert exp.size == cls.exponent_size

        bias = (1 << (cls.exponent_size - 1)) - 1

        if exp == 0:
            if mantissa != 0:
                if not cls.ieee_compliance:
                    warnings.warn('denorm will be flushed to 0')
                    if sign[0]:
                        return cls('-0')
                    else:
                        return cls('0')
                else:
                    exp = 1 - bias
                    s = ['-0.' if sign[0] else '0.', mantissa.binary_string()]
                    s.append('e')
                    s.append(str(exp))
                    return cls(gmpy2.mpfr(''.join(s),cls.mantissa_size+1, 2))
            elif sign[0]:
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
                if not cls.ieee_compliance:
                    warnings.warn('NaN will be flushed to infinity')
                return cls('nan')
        else:
            #unbias the exponent
            exp = exp - bias

            s = ['-1.' if sign[0] else '1.', mantissa.binary_string()]
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

    @classmethod
    @set_context
    def random(cls, allow_inf=True) -> 'FPVector':
        bias = (1 << (cls.exponent_size - 1)) - 1
        if allow_inf:
            sign = random.choice([-1, 1])
            mantissa = gmpy2.mpfr_random(gmpy2.random_state()) + 1
            exp = random.randint(1-bias, bias+1)
            return cls(mantissa*sign*(gmpy2.mpfr(2)**gmpy2.mpfr(exp)))
        else:
            sign = random.choice([-1, 1])
            mantissa = gmpy2.mpfr_random(gmpy2.random_state()) + 1
            exp = random.randint(1-bias, bias)
            return cls(mantissa*sign*(gmpy2.mpfr(2)**gmpy2.mpfr(exp)))
