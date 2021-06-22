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


def bit_cast(fn : tp.Callable[['XBit', 'XBit'], 'XBit']) -> tp.Callable[['XBit', tp.Any], 'XBit']:
    @functools.wraps(fn)
    def wrapped(self : 'XBit', other : tp.Any) -> 'XBit':
        if isinstance(other, XBit):
            return fn(self, other)
        else:
            try:
                other = XBit(other)
            except TypeError:
                return NotImplemented
            return fn(self, other)
    return wrapped


class _Xvalued(tp.Protocol):
    @property
    def _is_x(self) -> bool:
        ...

class _X:
    def __repr__(self) -> str:
        return 'x'

x = _X()


def preserve_x_unary(fn: tp.Callable[[_Xvalued], tp.Any]
        ) -> tp.Callable[[_Xvalued], tp.Any]:
    @functools.wraps(fn)
    def wrapped(self: _Xvalued) -> tp.Any:
        if self._is_x:
            return type(self)(x)
        else:
            return fn(self)
    return wrapped


def preserve_x_binary(fn: tp.Callable[[_Xvalued, _Xvalued], tp.Any]
        ) -> tp.Callable[[_Xvalued, _Xvalued], tp.Any]:
    @functools.wraps(fn)
    def wrapped(self: _Xvalued, other: _Xvalued) -> tp.Any:
        if self._is_x or other._is_x:
            return type(self)(x)
        else:
            return fn(self, other)
    return wrapped

def preserve_x_binary_bit(fn: tp.Callable[[_Xvalued, _Xvalued], AbstractBit]
        ) -> tp.Callable[[_Xvalued, _Xvalued], AbstractBit]:
    @functools.wraps(fn)
    def wrapped(self: _Xvalued, other: _Xvalued) -> tp.Any:
        if self._is_x or other._is_x:
            return self.get_family().Bit(x)
        else:
            return fn(self, other)
    return wrapped

class XBit(AbstractBit):
    @staticmethod
    def get_family() -> TypeFamily:
        return _Family_

    def __init__(self, value=x):
        if value is x:
            self._value = value
        elif isinstance(value,XBit):
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

    @preserve_x_unary
    def __invert__(self) -> 'XBit':
        return type(self)(not self._value)

    @bit_cast
    @preserve_x_binary
    def __eq__(self, other) -> 'XBit':
        return type(self)(self._value == other._value)

    @bit_cast
    @preserve_x_binary
    def __ne__(self, other) -> 'XBit':
        return type(self)(self._value != other._value)

    @bit_cast
    def __and__(self, other) -> 'XBit':
        if self._is_x and other._is_x:
            return type(self)(x)
        elif self._is_x and not other or other._is_x and not self:
            return type(self)(False)
        elif self._is_x or other._is_x:
            return type(self)(x)
        else:
            return type(self)(self._value & other._value)

    @bit_cast
    def __or__(self, other) -> 'XBit':
        if self._is_x and other._is_x:
            return type(self)(x)
        elif self._is_x and other or other._is_x and self:
            return type(self)(True)
        elif self._is_x or other._is_x:
            return type(self)(x)
        else:
            return type(self)(self._value & other._value)

    @bit_cast
    @preserve_x_binary
    def __xor__(self, other) -> 'XBit':
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
        if self._is_x:
            raise NotImplementedError()

        def _ite(select, t_branch, f_branch):
            return t_branch if select else f_branch

        return build_ite(_ite, self, t_branch, f_branch)

    def __bool__(self) -> bool:
        if self._is_x:
            raise ValueError("Cannot cast x to bool")
        return self._value

    def __int__(self) -> int:
        if self._is_x:
            raise ValueError("Cannot cast x to int")
        return int(self._value)

    def __repr__(self) -> str:
        if self._value is not None:
            return f'{type(self).__name__}({self._value})'
        else:
            return f'{type(self).__name__}(x)'

    def __hash__(self) -> int:
        return hash((type(self), self._value))

    @property
    def _is_x(self):
        return self._value is x

def _coerce(T : tp.Type['XBitVector'], val : tp.Any) -> 'XBitVector':
    if not isinstance(val,XBitVector):
        return T(val)
    elif val.size != T.size:
        raise InconsistentSizeError('Inconsistent size')
    else:
        return val

def bv_cast(fn : tp.Callable[['XBitVector', 'XBitVector'], tp.Any]) -> tp.Callable[['XBitVector', tp.Any], tp.Any]:
    @functools.wraps(fn)
    def wrapped(self : 'XBitVector', other : tp.Any) -> tp.Any:
        other = _coerce(type(self), other)
        return fn(self, other)
    return wrapped


class XBitVector(AbstractBitVector):
    @staticmethod
    def get_family() -> TypeFamily:
        return _Family_

    def __init__(self, value=x):
        if value is x:
            self._value = x
            return
        elif isinstance(value, XBitVector):
            if value.size > self.size:
                warnings.warn('Truncating value from {} to {}'.format(type(value), type(self)), stacklevel=3)
            value = value._value
        elif isinstance(value, XBit):
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
        return hash((type(self), self._value))

    def __str__(self):
        return str(int(self))

    def __repr__(self):
        return f'{type(self).__name__}({self._value})'

    @property
    def value(self):
        return self._value

    def __setitem__(self, index: int, value: tp.Union[bool, XBit, int]):
        if self._is_x or isinstance(index, slice):
            raise NotImplementedError()

        if not isinstance(index, int):
            raise TypeError(f'I ndex must be of type int')

        if not (isinstance(value, bool) or isinstance(value, XBit) or (isinstance(value, int) and value in {0, 1})):
            raise ValueError("Second argument __setitem__ on a single BitVector index should be a boolean or 0 or 1, not {value}".format(value=value))

        if isinstance(value,XBit) and value._is_x:
            self._vaue = x

        if index < 0:
            index = self.size+index

        if not (0 <= index < self.size):
            raise IndexError()

        mask = type(self)(1 << index)
        self._value = XBit(value).ite(self | mask,  self & ~mask)._value

    def __getitem__(self, index : tp.Union[int, slice]) -> tp.Union['XBitVector', XBit]:
        if isinstance(index, slice):
            v = self.bits()[index]
            return type(self).unsized_t[len(v)](v)
        elif isinstance(index, int):
            if index < 0:
                index = self.size+index
            if not (0 <= index < self.size):
                raise IndexError()
            return XBit((self._value >> index) & 1)
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

        if self._is_x or other._is_x:
            val = x
        else:
            val = self.value | (other.value << self.size)

        return T[self.size+other.size](val)

    def bvnot(self):
        return type(self)(~self.as_uint())

    @bv_cast
    @preserve_x_binary
    def bvand(self, other: 'XBitVector') -> 'XBitVector':
        return type(self)(self.as_uint() & other.as_uint())

    @bv_cast
    @preserve_x_binary
    def bvor(self, other: 'XBitVector') -> 'XBitVector':
        return type(self)(self.as_uint() | other.as_uint())

    @bv_cast
    def bvxor(self, other: 'XBitVector') -> 'XBitVector':
        return type(self)(self.as_uint() ^ other.as_uint())

    @bv_cast
    @preserve_x_binary
    def bvshl(self, other: 'XBitVector') -> 'XBitVector':
        return type(self)(self.as_uint() << other.as_uint())

    @bv_cast
    @preserve_x_binary
    def bvlshr(self, other: 'XBitVector') -> 'XBitVector':
        return type(self)(self.as_uint() >> other.as_uint())

    @bv_cast
    @preserve_x_binary
    def bvashr(self, other: 'XBitVector') -> 'XBitVector':
        return type(self)(self.as_sint() >> other.as_uint())

    @bv_cast
    @preserve_x_binary
    def bvrol(self, other: 'XBitVector') -> 'XBitVector':
        other = (len(self) - other.as_uint()) % len(self)
        return self[other:].concat(self[:other])

    @bv_cast
    @preserve_x_binary
    def bvror(self, other: 'XBitVector') -> 'XBitVector':
        other = other.as_uint() % len(self)
        return self[other:].concat(self[:other])

    @bv_cast
    @preserve_x_binary
    def bvcomp(self, other: 'XBitVector') -> 'XBitVector':
        return type(self).unsized_t[1](self.as_uint() == other.as_uint())

    @bv_cast
    @preserve_x_binary_bit
    def bveq(self, other: 'XBit') -> 'XBitVector':
        return self.get_family().Bit(self.as_uint() == other.as_uint())

    @bv_cast
    @preserve_x_binary_bit
    def bvult(self, other: 'XBit') -> 'XBitVector':
        return self.get_family().Bit(self.as_uint() < other.as_uint())

    @bv_cast
    @preserve_x_binary_bit
    def bvslt(self, other: 'XBit') -> 'XBitVector':
        return self.get_family().Bit(self.as_sint() < other.as_sint())

    @preserve_x_binary
    def bvneg(self):
        return type(self)(~self.as_uint() + 1)


    def adc(self, other: 'XBitVector', carry: XBit) -> tp.Tuple['XBitVector',XBit]:
        """
        add with carry

        returns a two element tuple of the form (result, carry)

        """
        if self._is_x or other._is_x or carry._is_x:
            return type(self)(x), self.get_family().Bit(x)
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
    def bvadd(self, other: 'XBitVector') -> 'XBitVector':
        return type(self)(self.as_uint() + other.as_uint())

    @bv_cast
    def bvsub(self, other: 'XBitVector') -> 'XBitVector':
        return type(self)(self.as_uint() - other.as_uint())

    @bv_cast
    def bvmul(self, other: 'XBitVector') -> 'XBitVector':
        return type(self)(self.as_uint() * other.as_uint())

    @bv_cast
    def bvudiv(self, other: 'XBitVector') -> 'XBitVector':
        other = other.as_uint()
        if other == 0:
            return type(self)((1 << self.size) - 1)
        return type(self)(self.as_uint() // other)

    @bv_cast
    def bvurem(self, other: 'XBitVector') -> 'XBitVector':
        other = other.as_uint()
        if other == 0:
            return self
        return type(self)(self.as_uint() % other)

    # bvumod

    @bv_cast
    def bvsdiv(self, other: 'XBitVector') -> 'XBitVector':
        other = other.as_sint()
        if other == 0:
            return type(self)((1 << self.size) - 1)
        return type(self)(self.as_sint() // other)

    @bv_cast
    def bvsrem(self, other: 'XBitVector') -> 'XBitVector':
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
        return XBitVector[width](random.randint(0, (1 << width) - 1))

    @property
    def _is_x(self):
        return self._value is x


class XNumVector(XBitVector):
    __hash__ = XBitVector.__hash__


class XUIntVector(XNumVector):
    __hash__ = XNumVector.__hash__

    @staticmethod
    def random(width):
        return UIntVector[width](random.randint(0, (1 << width) - 1))


class XSIntVector(XNumVector):
    __hash__ = XNumVector.__hash__

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

_Family_ = TypeFamily(XBit, XBitVector, XUIntVector, XSIntVector)
