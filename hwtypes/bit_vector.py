import typing as tp
from .bit_vector_abc import AbstractBitVector, AbstractBit, TypeFamily, InconsistentSizeError
from .bit_vector_util import build_ite
from .compatibility import IntegerTypes, StringTypes

import functools
import random
import warnings

#
# seq to int
#
def seq2int(l : tp.Sequence):
    value = 0
    for idx,v in enumerate(l):
        value |= int(bool(v)) << idx
    return value

#
# int to seq
#
def int2seq(value : int, n : int):
    return [(value >> i) & 1 for i in range(n)]


def bit_cast(fn : tp.Callable[['Bit', 'Bit'], 'Bit']) -> tp.Callable[['Bit', tp.Union['Bit', bool]], 'Bit']:
    @functools.wraps(fn)
    def wrapped(self : 'Bit', other : tp.Union['Bit', bool]) -> 'Bit':
        if isinstance(other, Bit):
            return fn(self, other)
        else:
            try:
                other = Bit(other)
            except TypeError:
                return NotImplemented
            return fn(self, other)
    return wrapped


class Bit(AbstractBit):
    @staticmethod
    def get_family() -> TypeFamily:
        return _Family_

    def __init__(self, value):
        if isinstance(value, Bit):
            self._value = value._value
        elif isinstance(value, bool):
            self._value = value
        elif isinstance(value, int):
            if value not in {0, 1}:
                raise ValueError('Bit must have value 0 or 1 not {}'.format(value))
            self._value = bool(value)
        elif hasattr(value, '__bool__'):
            self._value = bool(value)
        else:
            raise TypeError("Can't coerce {} to Bit".format(type(value)))

    def __invert__(self):
        return type(self)(not self._value)

    @bit_cast
    def __eq__(self, other):
        return type(self)(self._value == other._value)

    @bit_cast
    def __ne__(self, other):
        return type(self)(self._value != other._value)

    @bit_cast
    def __and__(self, other):
        return type(self)(self._value & other._value)

    @bit_cast
    def __or__(self, other):
        return type(self)(self._value | other._value)

    @bit_cast
    def __xor__(self, other):
        return type(self)(self._value ^ other._value)

    def ite(self, t_branch, f_branch):
        '''
        typing works as follows:
            if t_branch and f_branch are both Bit[Vector] types
            from the same family, and type(t_branch) is type(f_branch),
            then return type is t_branch.

            elif t_branch and f_branch are both Bit[Vector] types
            from the same family, then return type is a polymorphic
            type.

            elif t_brand and f_branch are tuples of the
            same length, then these rules are applied recursively

            else there is an error

        '''
        def _ite(select, t_branch, f_branch):
            return t_branch if select else f_branch

        return build_ite(_ite, self, t_branch, f_branch)

    def __bool__(self) -> bool:
        return self._value

    def __int__(self) -> int:
        return int(self._value)

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._value})'

    def __hash__(self) -> int:
        return hash((type(self), self._value))

    @classmethod
    def random(cls) -> AbstractBit:
        return cls(random.getrandbits(1))

def _coerce(T : tp.Type['BitVector'], val : tp.Any) -> 'BitVector':
    if not isinstance(val, BitVector):
        return T(val)
    elif val.size != T.size:
        raise InconsistentSizeError('Inconsistent size')
    else:
        return val

def bv_cast(fn : tp.Callable[['BitVector', 'BitVector'], tp.Any]) -> tp.Callable[['BitVector', tp.Any], tp.Any]:
    @functools.wraps(fn)
    def wrapped(self : 'BitVector', other : tp.Any) -> tp.Any:
        other = _coerce(type(self), other)
        return fn(self, other)
    return wrapped

class BitVector(AbstractBitVector):
    @staticmethod
    def get_family() -> TypeFamily:
        return _Family_

    def __init__(self, value=0):
        if isinstance(value, BitVector):
            if value.size > self.size:
                warnings.warn('Truncating value from {} to {}'.format(type(value), type(self)), stacklevel=3)
            value = value._value
        elif isinstance(value, Bit):
            value = int(bool(value))
        elif isinstance(value, IntegerTypes):
            if value.bit_length() > self.size:
                pass
                #This warning would be trigger constantly
                #warnings.warn('Truncating value {} to {}'.format(value, type(self)))
        elif isinstance(value, tp.Sequence):
            if len(value) > self.size:
                warnings.warn('Truncating value {} to {}'.format(value, type(self)), stacklevel=3)
            value = seq2int(value)
        elif hasattr(value, '__int__'):
            value = int(value)
            if value.bit_length() > self.size:
                warnings.warn('Truncating value {} to {}'.format(value, type(self)), stacklevel=3)
        else:
            raise TypeError('Cannot construct {} from {}'.format(type(self), value))
        mask = (1 << self.size) - 1
        self._value = value & mask

    @classmethod
    def make_constant(cls, value, size=None):
        if size is None:
            return cls(value)
        else:
            return cls.unsized_t[size](value)

    def __hash__(self):
        return hash(f"{type(self)}{self._value}")

    def __str__(self):
        return str(int(self))

    def __repr__(self):
        return f'{type(self).__name__}({self._value})'

    @property
    def value(self):
        return self._value

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            raise NotImplementedError()
        else:
            if not (isinstance(value, bool) or isinstance(value, Bit) or (isinstance(value, int) and value in {0, 1})):
                raise ValueError("Second argument __setitem__ on a single BitVector index should be a boolean or 0 or 1, not {value}".format(value=value))

            if index < 0:
                index = self.size+index

            if not (0 <= index < self.size):
                raise IndexError()

            mask = type(self)(1 << index)
            self._value = Bit(value).ite(self | mask,  self & ~mask)._value

    def __getitem__(self, index : tp.Union[int, slice]) -> tp.Union['BitVector', Bit]:
        if isinstance(index, slice):
            v = self.bits()[index]
            return type(self).unsized_t[len(v)](v)
        elif isinstance(index, int):
            if index < 0:
                index = self.size+index
            if not (0 <= index < self.size):
                raise IndexError()
            return Bit((self._value >> index) & 1)
        else:
            raise TypeError()

    @property
    def num_bits(self):
        return self.size

    def __len__(self):
        return self.size

    def concat(self, other):
        T = type(self).unsized_t
        if not isinstance(other, T):
            raise TypeError(f'value must of type {T}')
        return T[self.size+other.size](self.value | (other.value << self.size))

    def bvnot(self):
        return type(self)(~self.as_uint())

    @bv_cast
    def bvand(self, other):
        return type(self)(self.as_uint() & other.as_uint())

    @bv_cast
    def bvor(self, other):
        return type(self)(self.as_uint() | other.as_uint())

    @bv_cast
    def bvxor(self, other):
        return type(self)(self.as_uint() ^ other.as_uint())

    @bv_cast
    def bvshl(self, other):
        return type(self)(self.as_uint() << other.as_uint())

    @bv_cast
    def bvlshr(self, other):
        return type(self)(self.as_uint() >> other.as_uint())

    @bv_cast
    def bvashr(self, other):
        return type(self)(self.as_sint() >> other.as_uint())

    @bv_cast
    def bvrol(self, other):
        other = (len(self) - other.as_uint()) % len(self)
        return self[other:].concat(self[:other])

    @bv_cast
    def bvror(self, other):
        other = other.as_uint() % len(self)
        return self[other:].concat(self[:other])

    @bv_cast
    def bvcomp(self, other):
        return type(self).unsized_t[1](self.as_uint() == other.as_uint())

    @bv_cast
    def bveq(self, other):
        return self.get_family().Bit(self.as_uint() == other.as_uint())

    @bv_cast
    def bvult(self, other):
        return self.get_family().Bit(self.as_uint() < other.as_uint())

    @bv_cast
    def bvslt(self, other):
        return self.get_family().Bit(self.as_sint() < other.as_sint())

    def bvneg(self):
        return type(self)(~self.as_uint() + 1)


    def adc(self, other : 'BitVector', carry : Bit) -> tp.Tuple['BitVector', Bit]:
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
        return type(self)(self.as_uint() + other.as_uint())

    @bv_cast
    def bvsub(self, other):
        return type(self)(self.as_uint() - other.as_uint())

    @bv_cast
    def bvmul(self, other):
        return type(self)(self.as_uint() * other.as_uint())

    @bv_cast
    def bvudiv(self, other):
        other = other.as_uint()
        if other == 0:
            return type(self)((1 << self.size) - 1)
        return type(self)(self.as_uint() // other)

    @bv_cast
    def bvurem(self, other):
        other = other.as_uint()
        if other == 0:
            return self
        return type(self)(self.as_uint() % other)

    # bvumod

    @bv_cast
    def bvsdiv(self, other):
        other = other.as_sint()
        if other == 0:
            return type(self)((1 << self.size) - 1)
        return type(self)(self.as_sint() // other)

    @bv_cast
    def bvsrem(self, other):
        other = other.as_sint()
        if other == 0:
            return self
        return type(self)(self.as_sint() % other)

    # bvsmod
    def __invert__(self): return self.bvnot()

    def __and__(self, other):
        try:
            return self.bvand(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __or__(self, other):
        try:
            return self.bvor(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __xor__(self, other):
        try:
            return self.bvxor(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented


    def __lshift__(self, other):
        try:
            return self.bvshl(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __rshift__(self, other):
        try:
            return self.bvlshr(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __neg__(self): return self.bvneg()

    def __add__(self, other):
        try:
            return self.bvadd(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __sub__(self, other):
        try:
            return self.bvsub(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __mul__(self, other):
        try:
            return self.bvmul(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __floordiv__(self, other):
        try:
            return self.bvudiv(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __mod__(self, other):
        try:
            return self.bvurem(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented


    def __eq__(self, other):
        try:
            return self.bveq(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __ne__(self, other):
        try:
            return self.bvne(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __ge__(self, other):
        try:
            return self.bvuge(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __gt__(self, other):
        try:
            return self.bvugt(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __le__(self, other):
        try:
            return self.bvule(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __lt__(self, other):
        try:
            return self.bvult(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError as e:
            return NotImplemented

    def as_uint(self):
        return self._value

    def as_sint(self):
        value = self._value
        if self[-1]:
            value = value - (1 << self.size)
        return value

    as_int = as_sint

    def __int__(self):
        return self.as_uint()

    def __bool__(self):
        return bool(int(self))

    def binary_string(self):
        return "".join(str(int(i)) for i in reversed(self.bits()))

    def as_binary_string(self):
        return "0b" + self.binary_string()

    def bits(self):
        return int2seq(self._value, self.size)

    def as_bool_list(self):
        return [bool(x) for x in self.bits()]

    def repeat(self, r):
        r = int(r)
        if r <= 0:
            raise ValueError()

        return type(self).unsized_t[r * self.size](r * self.bits())

    def sext(self, ext):
        ext = int(ext)
        if ext < 0:
            raise ValueError()

        T = type(self).unsized_t
        return self.concat(T[1](self[-1]).repeat(ext))

    def ext(self, ext):
        return self.zext(ext)

    def zext(self, ext):
        ext = int(ext)
        if ext < 0:
            raise ValueError()

        T = type(self).unsized_t
        return self.concat(T[ext](0))

    @staticmethod
    def random(width):
        return BitVector[width](random.randint(0, (1 << width) - 1))


class NumVector(BitVector):
    __hash__ = BitVector.__hash__


class UIntVector(NumVector):
    __hash__ = NumVector.__hash__

    @staticmethod
    def random(width):
        return UIntVector[width](random.randint(0, (1 << width) - 1))


class SIntVector(NumVector):
    __hash__ = NumVector.__hash__

    def __int__(self):
        return self.as_sint()

    def __rshift__(self, other):
        try:
            return self.bvashr(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __floordiv__(self, other):
        try:
            return self.bvsdiv(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __mod__(self, other):
        try:
            return self.bvsrem(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __ge__(self, other):
        try:
            return self.bvsge(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __gt__(self, other):
        try:
            return self.bvsgt(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __lt__(self, other):
        try:
            return self.bvslt(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __le__(self, other):
        try:
            return self.bvsle(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    @staticmethod
    def random(width):
        w = width - 1
        return SIntVector[width](random.randint(-(1 << w), (1 << w) - 1))

    def ext(self, other):
        return self.sext(other)

def overflow(a, b, res):
    msb_a = a[-1]
    msb_b = b[-1]
    N = res[-1]
    return (msb_a & msb_b & ~N) | (~msb_a & ~msb_b & N)

_Family_ = TypeFamily(Bit, BitVector, UIntVector, SIntVector)
