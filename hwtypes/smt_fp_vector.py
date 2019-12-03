import weakref

import pysmt
import pysmt.shortcuts as shortcuts
from pysmt.typing import  BVType, BOOL, FunctionType

from .smt_bit_vector import SMTBit, SMTBitVector, SMTSIntVector, SMYBOLIC, AUTOMATIC
from .fp_vector_abc import AbstractFPVector, RoundingMode

# using None to represent cls
_SIGS = [
    ('fp_abs', None, None,),
    ('fp_neg', None, None,),
    ('fp_add', None, None, None,),
    ('fp_sub', None, None, None,),
    ('fp_mul', None, None, None,),
    ('fp_div', None, None, None,),
    ('fp_fma', None, None, None, None,),
    ('fp_sqrt', None, None,),
    ('fp_rem', None, None,None),
    ('fp_round_to_integral', None, None,),
    ('fp_min', None, None,),
    ('fp_max', None, None,),
    ('fp_leq', None, None, BOOL,),
    ('fp_lt', None, None, BOOL,),
    ('fp_geq', None, None, BOOL,),
    ('fp_gt', None, None, BOOL,),
    ('fp_eq', None, None, BOOL,),
    ('fp_is_normal', None, BOOL,),
    ('fp_is_subnormal', None, BOOL,),
    ('fp_is_zero', None, BOOL,),
    ('fp_is_infinite', None, BOOL,),
    ('fp_is_NaN', None, BOOL,),
    ('fp_is_negative', None, BOOL,),
    ('fp_is_positive', None, BOOL,),
]

_name_table = weakref.WeakValueDictionary()
_uf_table = weakref.WeakKeyDictionary()


class SMTFPVector(AbstractFPVector):
    def __init__(self, value=SMYBOLIC, *, name=AUTOMATIC):
        if name is not AUTOMATIC and value is not SMYBOLIC:
            raise TypeError('Can only name symbolic variables')
        elif name is not AUTOMATIC:
            if not isinstance(name, str):
                raise TypeError('Name must be string')
            elif name in _name_table:
                raise ValueError(f'Name {name} already in use')
            _name_table[name] = self

        T = BVType(self.size)

        if value is SMYBOLIC:
            if name is AUTOMATIC:
                value = shortcuts.FreshSymbol(T)
            else:
                value = shortcuts.Symbol(name, T)
        elif isinstance(value, pysmt.fnode.FNode):
            t = value.get_type()
            if t is not T:
                raise TypeError(f'Expected {T} not {t}')
        elif isinstance(value, type(self)):
            value = value._value
        elif isinstance(value, int):
            value = shortcuts.BV(value, self.size)
        else:
            raise TypeError(f"Can't coerce {value} to SMTFPVector")

        self._name = name
        self._value = value

    def __init_subclass__(cls):
        _uf_table[cls] = ufs = dict()
        T = BVType(cls.size)
        for method_name, *args in _SIGS:
            args = [T if x is None else x for x in args]
            rtype = args[-1]
            params = args[:-1]
            name = '.'.join((cls.__name__, method_name))
            ufs[method_name] = shortcuts.Symbol(name, FunctionType(rtype, params))

        ufs['to_sbv'] = dict()
        ufs['to_ubv'] = dict()

    @classmethod
    def _fp_method(cls, method_name, *args):
        uf = _uf_table[cls][method_name]
        return cls(uf(*args))

    @classmethod
    def _bit_method(cls, method_name, *args):
        uf = _uf_table[cls][method_name]
        return SMTBit(uf(*args))

    def fp_abs(self) -> 'SMTFPVector':
        return self._fp_method('fp_abs', self._value)

    def fp_neg(self) -> 'SMTFPVector':
        return self._fp_method('fp_neg', self._value)

    def fp_add(self, other: 'SMTFPVector') -> 'SMTFPVector':
        return self._fp_method('fp_add', self._value, other._value)

    def fp_sub(self, other: 'SMTFPVector') -> 'SMTFPVector':
        return self._fp_method('fp_sub', self._value, other._value)

    def fp_mul(self, other: 'SMTFPVector') -> 'SMTFPVector':
        return self._fp_method('fp_mul', self._value, other._value)

    def fp_div(self, other: 'SMTFPVector') -> 'SMTFPVector':
        return self._fp_method('fp_div', self._value, other._value)

    def fp_fma(self, coef: 'SMTFPVector', offset: 'SMTFPVector') -> 'SMTFPVector':
        return self._fp_method('fp_fma', self._value, coef._value, offset._value)

    def fp_sqrt(self) -> 'SMTFPVector':
        return self._fp_method('fp_sqrt', self._value)

    def fp_rem(self, other: 'SMTFPVector') -> 'SMTFPVector':
        return self._fp_method('fp_rem', self._value, other._value)

    def fp_round_to_integral(self) -> 'SMTFPVector':
        return self._fp_method('fp_round_to_integral', self._value)

    def fp_min(self, other: 'SMTFPVector') -> 'SMTFPVector':
        return self._fp_method('fp_min', self._value, other._value)

    def fp_max(self, other: 'SMTFPVector') -> 'SMTFPVector':
        return self._fp_method('fp_max', self._value, other._value)

    def fp_leq(self, other: 'SMTFPVector') ->  SMTBit:
        return self._bit_method('fp_leq', self._value, other._value)

    def fp_lt(self, other: 'SMTFPVector') ->  SMTBit:
        return self._bit_method('fp_lt', self._value, other._value)

    def fp_geq(self, other: 'SMTFPVector') ->  SMTBit:
        return self._bit_method('fp_geq', self._value, other._value)

    def fp_gt(self, other: 'SMTFPVector') ->  SMTBit:
        return self._bit_method('fp_gt', self._value, other._value)

    def fp_eq(self, other: 'SMTFPVector') ->  SMTBit:
        return self._bit_method('fp_eq', self._value, other._value)

    def fp_is_normal(self) -> SMTBit:
        return self._bit_method('fp_is_normal', self._value)

    def fp_is_subnormal(self) -> SMTBit:
        return self._bit_method('fp_is_subnormal', self._value)

    def fp_is_zero(self) -> SMTBit:
        return self._bit_method('fp_is_zero', self._value)

    def fp_is_infinite(self) -> SMTBit:
        return self._bit_method('fp_is_infinite', self._value)

    def fp_is_NaN(self) -> SMTBit:
        return self._bit_method('fp_is_NaN', self._value)

    def fp_is_negative(self) -> SMTBit:
        return self._bit_method('fp_is_negative', self._value)

    def fp_is_positive(self) -> SMTBit:
        return self._bit_method('fp_is_positive', self._value)

    def to_ubv(self, size : int) -> SMTBitVector:
        cls = type(self)
        ufs = _uf_table[cls]['to_ubv']
        if size not in ufs:
            name = '.'.join((cls.__name__, f'to_ubv[{size}]'))
            ufs[size] = shortcuts.Symbol(
                name,
                FunctionType(BVType(size), (BVType(self.size),))
            )

        return SMTBitVector[size](ufs[size](self._value))

    def to_sbv(self, size : int) -> SMTBitVector:
        cls = type(self)
        ufs = _uf_table[cls]['to_usbv']
        if size not in ufs:
            name = '.'.join((cls.__name__, f'to_sbv[{size}]'))
            ufs[size] = shortcuts.Symbol(
                name,
                FunctionType(BVType(size), (BVType(self.size),))
            )

        return SMTBitVector[size](ufs[size](self._value))

    def reinterpret_as_bv(self) -> SMTBitVector:
        return SMTBitVector[self.size](self._value)

    @classmethod
    def reinterpret_from_bv(cls, value: SMTBitVector) -> 'SMTFPVector':
        return cls(value._value)

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
