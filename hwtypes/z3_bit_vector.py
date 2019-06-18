import hwtypes as ht
import typing as tp
import itertools as it
import functools as ft
from .bit_vector_abc import AbstractBitVector, AbstractBit, TypeFamily

from abc import abstractmethod

import z3

import re
import warnings
import weakref

import random

__ALL__ = ['z3BitVector', 'z3NumVector', 'z3SIntVector', 'z3UIntVector']

_var_counter = it.count()
_name_table = weakref.WeakValueDictionary()
_free_names = []

def _gen_name():
    if _free_names:
        return _free_names.pop()
    name = f'V_{next(_var_counter)}'
    while name in _name_table:
        name = f'V_{next(_var_counter)}'
    return name

_name_re = re.compile(r'V_\d+')

class _SMYBOLIC:
    def __repr__(self):
        return 'SYMBOLIC'

class _AUTOMATIC:
    def __repr__(self):
        return 'AUTOMATIC'

SMYBOLIC = _SMYBOLIC()
AUTOMATIC = _AUTOMATIC()

def bit_cast(fn):
    @ft.wraps(fn)
    def wrapped(self, other):
        if isinstance(other, z3Bit):
            return fn(self, other)
        else:
            return fn(self, z3Bit(other))
    return wrapped

class z3Bit(AbstractBit):
    @staticmethod
    def get_family() -> ht.TypeFamily:
        return _Family_

    def __init__(self, value=SMYBOLIC, *, name=AUTOMATIC):
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

        if value is SMYBOLIC:
            self._value = z3.Bool(name)
        elif isinstance(value, z3.BoolRef):
            self._value = value
        elif isinstance(value, z3Bit):
            if name is not AUTOMATIC and name != value.name:
                warnings.warn('Changing the name of a z3Bit does not cause a new underlying smt variable to be created')
            self._value = value._value
        elif isinstance(value, bool):
            self._value = z3.BoolVal(value)
        elif isinstance(value, int):
            if value not in {0, 1}:
                raise ValueError('Bit must have value 0 or 1 not {}'.format(value))
            self._value = z3.BoolVal(bool(value))
        elif hasattr(value, '__bool__'):
            self._value = z3.BoolVal(bool(value))
        else:
            raise TypeError("Can't coerce {} to Bit".format(type(value)))

        self._name = name
        self._value = z3.simplify(self._value)

    def __repr__(self):
        if self._name is not AUTOMATIC:
            return f'{type(self)}({self._name})'
        else:
            return f'{type(self)}({self._value})'

    @property
    def value(self):
        return self._value

    @bit_cast
    def __eq__(self, other : 'z3Bit') -> 'z3Bit':
        return type(self)(self.value == other.value)

    @bit_cast
    def __ne__(self, other : 'z3Bit') -> 'z3Bit':
        return type(self)(self.value != other.value)

    def __invert__(self) -> 'z3Bit':
        return type(self)(z3.Not(self.value))

    @bit_cast
    def __and__(self, other : 'z3Bit') -> 'z3Bit':
        return type(self)(z3.And(self.value, other.value))

    @bit_cast
    def __or__(self, other : 'z3Bit') -> 'z3Bit':
        return type(self)(z3.Or(self.value, other.value))

    @bit_cast
    def __xor__(self, other : 'z3Bit') -> 'z3Bit':
        return type(self)(z3.Xor(self.value, other.value))

    def ite(self, t_branch, f_branch):
        tb_t = type(t_branch)
        fb_t = type(f_branch)
        BV_t = self.get_family().BitVector
        if isinstance(t_branch, BV_t) and isinstance(f_branch, BV_t):
            if tb_t is not fb_t:
                raise TypeError('Both branches must have the same type')
            T = tb_t
        elif isinstance(t_branch, BV_t):
            f_branch = tb_t(f_branch)
            T = tb_t
        elif isinstance(f_branch, BV_t):
            t_branch = fb_t(t_branch)
            T = fb_t
        else:
            t_branch = BV_t(t_branch)
            f_branch = BV_t(f_branch)
            ext = t_branch.size - f_branch.size
            if ext > 0:
                f_branch = f_branch.zext(ext)
            elif ext < 0:
                t_branch = t_branch.zext(-ext)

            T = type(t_branch)


        return T(z3.If(self.value, t_branch.value, f_branch.value))

def _coerce(T : tp.Type['z3BitVector'], val : tp.Any) -> 'z3BitVector':
    if not isinstance(val, z3BitVector):
        return T(val)
    elif val.size != T.size:
        raise TypeError('Inconsistent size')
    else:
        return val

def bv_cast(fn : tp.Callable[['z3BitVector', 'z3BitVector'], tp.Any]) -> tp.Callable[['z3BitVector', tp.Any], tp.Any]:
    @ft.wraps(fn)
    def wrapped(self : 'z3BitVector', other : tp.Any) -> tp.Any:
        other = _coerce(type(self), other)
        return fn(self, other)
    return wrapped

def int_cast(fn : tp.Callable[['z3BitVector', int], tp.Any]) -> tp.Callable[['z3BitVector', tp.Any], tp.Any]:
    @ft.wraps(fn)
    def wrapped(self :  'z3BitVector', other :  tp.Any) -> tp.Any:
        other = int(other)
        return fn(self, other)
    return wrapped

class z3BitVector(AbstractBitVector):
    @staticmethod
    def get_family() -> TypeFamily:
        return _Family_

    def __init__(self, value=SMYBOLIC, *, name=AUTOMATIC):
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
        self._name = name

        T = z3.BitVecSort(self.size)

        if value is SMYBOLIC:
            self._value = z3.BitVec(name, T)
        elif isinstance(value, z3.BitVecRef):
            t = value.sort()
            if t == T:
                self._value = value
            else:
                raise TypeError(f'Expected {T} not {t}')
        elif isinstance(value, z3BitVector):
            if name is not AUTOMATIC and name != value.name:
                warnings.warn('Changing the name of a z3BitVector does not cause a new underlying smt variable to be created')

            ext = self.size - value.size

            if ext < 0:
                warnings.warn('Truncating value from {} to {}'.format(type(value), type(self)))
                self._value = value[:self.size].value
            elif ext > 0:
                self._value = value.zext(ext).value
            else:
                self._value = value.value
        elif isinstance(value, z3.BoolRef):
            self._value = z3.If(value, z3.BitVecVal(1, T), z3.BitVecVal(0, T))

        elif isinstance(value, z3Bit):
            self._value = z3.If(value.value, z3.BitVecVal(1, T), z3.BitVecVal(0, T))

        elif isinstance(value, tp.Sequence):
            if len(value) != self.size:
                raise ValueError('Iterable is not the correct size')
            cls = type(self)
            B1 = cls.unsized_t[1]
            self._value = ft.reduce(lambda acc, elem : acc.concat(elem), map(B1, value)).value
        elif isinstance(value, int):
            self._value =  z3.BitVecVal(value, self.size)

        elif hasattr(value, '__int__'):
            value = int(value)
            self._value = z3.BitVecVal(value, self.size)
        else:
            raise TypeError("Can't coerce {} to z3BitVector".format(type(value)))

        self._value = z3.simplify(self._value)
        assert self._value.sort() == T

    def make_constant(self, value, size:tp.Optional[int]=None):
        if size is None:
            size = self.size
        return type(self).unsized_t[size](value)

    @property
    def value(self):
        return self._value

    @property
    def num_bits(self):
        return self.size

    def __repr__(self):
        if self._name is not AUTOMATIC:
            return f'{type(self)}({self._name})'
        else:
            return f'{type(self)}({self._value})'

    def __getitem__(self, index):
        size = self.size
        if isinstance(index, slice):
            start, stop, step = index.start, index.stop, index.step

            if start is None:
                start = 0
            elif start < 0:
                start = size + start

            if stop is None:
                stop = size
            elif stop < 0:
                stop = size + stop

            stop = min(stop, size)

            if step is None:
                step = 1
            elif step != 1:
                raise IndexError('SMT extract does not support step != 1')

            v = z3.Extract(stop-1, start, self.value)
            return type(self).unsized_t[v.sort().size()](v)
        elif isinstance(index, int):
            if index < 0:
                index = size+index

            if not (0 <= index < size):
                raise IndexError()

            v = z3.Extract(index, index, self.value)
            return self.get_family().Bit(v == z3.BitVecVal(1, 1))
        else:
            raise TypeError()


    def __setitem__(self, index, value):
        if isinstance(index, slice):
            raise NotImplementedError()
        else:
            if not (isinstance(value, bool) or isinstance(value, z3Bit) or (isinstance(value, int) and value in {0, 1})):
                raise ValueError("Second argument __setitem__ on a single BitVector index should be a bit, boolean or 0 or 1, not {value}".format(value=value))

            if index < 0:
                index = self.size+index

            if not (0 <= index < self.size):
                raise IndexError()

            mask = type(self)(1 << index)
            self._value = z3Bit(value).ite(self | mask,  self & ~mask)._value


    def __len__(self):
        return self.size

    def concat(self, other):
        T = type(self).unsized_t
        if not isinstance(other, T):
            raise TypeError(f'value must of type {T}')
        return T[self.size + other.size](z3.Concat(other.value, self.value))

    def bvnot(self):
        return type(self)(~self.value)

    @bv_cast
    def bvand(self, other):
        return type(self)(self.value & other.value)

    @bv_cast
    def bvnand(self, other):
        return type(self)(~(self.value & other.value))

    @bv_cast
    def bvor(self, other):
        return type(self)(self.value | other.value)

    @bv_cast
    def bvnor(self, other):
        return type(self)(~(self.value | other.value))

    @bv_cast
    def bvxor(self, other):
        return type(self)(self.value ^ other.value)

    @bv_cast
    def bvxnor(self, other):
        return type(self)(~(self.value ^ other.value))

    @bv_cast
    def bvshl(self, other):
        return type(self)(self.value << other.value)

    @bv_cast
    def bvlshr(self, other):
        return type(self)(z3.LShR(self.value, other.value))

    @bv_cast
    def bvashr(self, other):
        return type(self)(self.value >> other.value)

    @bv_cast
    def bvrol(self, other):
        return type(self)(z3.RotateLeft(self.value, other.value))

    @bv_cast
    def bvror(self, other):
        return type(self)(z3.RotateRight(self.value, other.value))

    @bv_cast
    def bvcomp(self, other):
        return type(self).unsized_t[1](self.value == other.value)

    @bv_cast
    def bveq(self,  other):
        return self.get_family().Bit(self.value == other.value)

    @bv_cast
    def bvne(self, other):
        return self.get_family().Bit(self.value != other.value)

    @bv_cast
    def bvult(self, other):
        return self.get_family().Bit(z3.ULT(self.value, other.value))

    @bv_cast
    def bvule(self, other):
        return self.get_family().Bit(z3.ULE(self.value, other.value))

    @bv_cast
    def bvugt(self, other):
        return self.get_family().Bit(z3.UGT(self.value, other.value))

    @bv_cast
    def bvuge(self, other):
        return self.get_family().Bit(z3.UGE(self.value, other.value))

    @bv_cast
    def bvslt(self, other):
        return self.get_family().Bit(self.value < other.value)

    @bv_cast
    def bvsle(self, other):
        return self.get_family().Bit(self.value <= other.value)

    @bv_cast
    def bvsgt(self, other):
        return self.get_family().Bit(self.value > other.value)

    @bv_cast
    def bvsge(self, other):
        return self.get_family().Bit(self.value >= other.value)

    def bvneg(self):
        return type(self)(-self.value)

    def adc(self, other : 'z3BitVector', carry : z3Bit) -> tp.Tuple['z3BitVector', z3Bit]:
        """
        add with carry

        returns a two element tuple of the form (result, carry)

        """
        T = type(self)
        other = _coerce(T, other)
        carry = _coerce(T.unsized_t[1], carry)

        a = self.zext(1)
        b = other.zext(1)
        c = carry.zext(T.size)

        res = a + b + c
        return res[0:-1], res[-1]

    def ite(self, t_branch, f_branch):
        return self.bvne(0).ite(t_branch, f_branch)

    @bv_cast
    def bvadd(self, other):
        return type(self)(self.value + other.value)

    @bv_cast
    def bvsub(self, other):
        return type(self)(self.value - other.value)

    @bv_cast
    def bvmul(self, other):
        return type(self)(self.value * other.value)

    @bv_cast
    def bvudiv(self, other):
        return type(self)(z3.UDiv(self.value, other.value))

    @bv_cast
    def bvurem(self, other):
        return type(self)(z3.URem(self.value, other.value))

    @bv_cast
    def bvsdiv(self, other):
        return type(self)(self.value / other.value)

    @bv_cast
    def bvsrem(self, other):
        return type(self)(self.value % other.value)

    __invert__ = bvnot
    __and__ = bvand
    __or__ = bvor
    __xor__ = bvxor

    __lshift__ = bvshl
    __rshift__ = bvlshr

    __neg__ = bvneg
    __add__ = bvadd
    __sub__ = bvsub
    __mul__ = bvmul
    __floordiv__ = bvudiv
    __mod__ = bvurem

    __eq__ = bveq
    __ne__ = bvne
    __ge__ = bvuge
    __gt__ = bvugt
    __le__ = bvule
    __lt__ = bvult



    @int_cast
    def repeat(self, n):
        return type(self)(z3.RepeatBitVec(n, self.value))

    @int_cast
    def sext(self, ext):
        if ext < 0:
            raise ValueError()
        return type(self).unsized_t[self.size + ext](z3.SignExt(ext, self.value))

    def ext(self, ext):
        return self.zext(ext)

    @int_cast
    def zext(self, ext):
        if ext < 0:
            raise ValueError()
        return type(self).unsized_t[self.size + ext](z3.ZeroExt(ext, self.value))

# Used in testing
#    def bits(self):
#        return [(self >> i) & 1 for i in range(self.size)]
#
#    def __int__(self):
#        return self.as_uint()
#
#    def as_uint(self):
#        return self._value.as_long()
#
#    def as_sint(self):
#        return self._value.as_signed_long()
#
#    @classmethod
#    def random(cls, width):
#        return cls.unsized_t[width](random.randint(0, (1 << width) - 1))
#

class z3NumVector(z3BitVector):
    pass


class z3UIntVector(z3NumVector):
    pass

class z3SIntVector(z3NumVector):
    def __rshift__(self, other):
        return self.bvashr(other)

    def __floordiv__(self, other):
        return self.bvsdiv(other)

    def __mod__(self, other):
        return self.bvsrem(other)

    def __ge__(self, other):
        return self.bvsge(other)

    def __gt__(self, other):
        return self.bvsgt(other)

    def __lt__(self, other):
        return self.bvslt(other)

    def __le__(self, other):
        return self.bvsle(other)

_Family_ = ht.TypeFamily(z3Bit, z3BitVector, z3UIntVector, z3SIntVector)


