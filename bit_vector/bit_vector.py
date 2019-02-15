from .bit_vector_abc import AbstractBitVector
from .compatibility import IntegerTypes, StringTypes
import functools
import random

#
# seq to int
#
def seq2int(l):
    n = len(l)

    i = 0
    for j in range(n):
        if l[j]:
            i |= 1 << j
    return i

#
# int to seq
#
def int2seq(i, n=0):
    if isinstance(i, StringTypes):
        i = ord(i)

    # find minimum number of bits needed for i
    if n == 0:
        j = i
        while j:
            n += 1
            j >>= 1

    return [1 if i & (1 << j) else 0 for j in range(n)]


def unary(fn):
    @functools.wraps(fn)
    def wrapped(self):
        # cast type
        T = type(self)
        val =  fn(self)
        return val if val.size == 1 else T(val)

    return wrapped

def binary_no_cast(fn):
    @functools.wraps(fn)
    def wrapped(self, other):
        T = type(self)

        # promote bool and int
        if isinstance(other, (int, bool)):
            other = T(other)

        # type check
        if not (isinstance(other, BitVector) or isinstance(other, int) and other.bit_length() <= self.size):
            raise TypeError(fn, other)

        # handle binary x
        if isinstance(other, BitVector):
            if self._value is None and other._value is None:
                return T(1)
            elif self._value is None or other._value is None:
                raise Exception("Invalid use of X value")
        elif self._value is None:
            raise Exception("Invalid use of X value")

        return fn(self, other)
    return wrapped

def binary(fn):
    @functools.wraps(fn)
    def wrapped(self, other):
        T = type(self)
        # promote bool and int
        if isinstance(other, (int, bool)):
            other = T(other)

        # type check
        if not (isinstance(other, BitVector) or isinstance(other, int) and other.bit_length() <= self.size):
            raise TypeError(fn, other)

        # handle binary x
        if isinstance(other, BitVector):
            if self._value is None and other._value is None:
                return T(None)
            elif self._value is None or other._value is None:
                raise Exception("Invalid use of X value")
        elif self._value is None:
            raise Exception("Invalid use of X value")

        # cast type
        T = type(self)
        val =  fn(self, other)
        return val if val.size == 1 else T(val)

    return wrapped

def no_x(fn):
    @functools.wraps(fn)
    def wrapped(self, *args, **kwargs):
        if self._value is None:
            raise Exception("Invalid use of X value")
        return fn(self, *args, **kwargs)

    return wrapped

class BitVector(AbstractBitVector):
    def __init__(self, value=0):
        if isinstance(value, BitVector):
            self._value = value._value
            self._bits = int2seq(self._value, self.size)
        elif isinstance(value, IntegerTypes):
            self._value = value
            self._value &= (1 << self.size)-1
            self._bits = int2seq(value, self.size)
        elif isinstance(value, list):
            if not (all(x == 0 or x == 1 for x in value) or all(x == False or x == True for x in value)):
                raise Exception("BitVector list initialization must be a list of 0s and 1s or a list of True and False")
            self._value = seq2int(value)
            self._bits = value
        elif value is None:
            self._value = None
            self._bits = None
        else:
            raise Exception("BitVector initialization with type {} not supported".format(type(value)))

        if self._value is not None and self._value.bit_length() > self.size:
            raise Exception("BitVector initialized with too small a width")

    def make_constant(self, value, size=None):
        if size is None:
            size = self.size
        return type(self)[size](value)


    def __hash__(self):
        return hash(repr(self))

    def __str__(self):
        if self._value is None:
            return "X"
        else:
            return str(int(self))

    def __repr__(self):
        return "BitVector[{size}]({value})".format(value=self._value, size=self.size)

    @no_x
    def __setitem__(self, index, value):
        if isinstance(index, slice):
            raise NotImplementedError()
        else:
            if not (isinstance(value, bool) or isinstance(value, int) and value in {0, 1}):
                raise ValueError("Second argument __setitem__ on a single BitVector index should be a boolean or 0 or 1, not {value}".format(value=value))
            self._bits[index] = value
            self._value = seq2int(self._bits)

    @no_x
    def __getitem__(self, index):
        if isinstance(index, slice):
            v = self._bits[index]
            return BitVector[len(v)](v)
        else:
            return BitVector[1](self.bits()[index])

    @property
    def num_bits(self):
        return self.size

    def __len__(self):
        return self.size

    # Note: In concat(x, y), the MSB of the result is the MSB of x.
    @classmethod
    def concat(cls, x, y):
        return BitVector[x.size+y.size](y.bits() + x.bits())

    @unary
    def bvnot(self):
        if self._value is None:
            return type(self)(None)
        else:
            return type(self)(~self.as_uint())

    @binary
    def bvand(self, other):
        return type(self)(self.as_uint() & other.as_uint())


    @binary
    def bvor(self, other):
        return type(self)(self.as_uint() | other.as_uint())


    @binary
    def bvxor(self, other):
        return type(self)(self.as_uint() ^ other.as_uint())

    @binary
    def bvshl(self, other):
        return type(self)( self.as_uint() << other.as_uint())

    @binary
    def bvlshr(self, other):
        return type(self)( self.as_uint() >> other.as_uint())

    @binary
    def bvashr(self, other):
        return type(self)( self.as_sint() >> other.as_uint())

    @binary
    def bvrol(self, other):
        other = other.as_uint() % len(self)
        return self.concat( self[other:], self[0:other] )

    @binary
    def bvror(self, other):
        other = (len(self) - other.as_uint()) % len(self)
        return self.concat( self[other:], self[0:other] )

    @binary_no_cast
    def bvcomp(self, other):
        if isinstance(other, list):
            other = BitVector(other)

        #if self.is_x() and isinstance(other, BitVector) or \
        #        isinstance(other, list) and \
        #        all(isinstance(x, bool) for x in other):
        #    result = True
        #elif isinstance(other, list) and all(isinstance(x, bool) for x in other):
        #    result = self.as_bool_list() == other
        #elif isinstance(other, bool) and self.size == 1:
        #    result = self.as_bool_list()[0] == other
        return BitVector[1](self._value == other._value)

    @binary_no_cast
    def bvult(self, other):
        return BitVector[1](self.as_uint() < other.as_uint())

    @binary_no_cast
    def bvslt(self, other):
        return BitVector[1](self.as_sint() < other.as_sint())

    @unary
    def bvneg(self):
        if self._value is None:
            return type(self)(None)
        else:
            return type(self)(~self.as_uint()+1)

    def adc(a, b, c):
        """
        add with carry

        returns a two element tuple of the form (result, carry)

        no type checks yet
        """
        n = a.size
        a = a.zext(1)
        b = b.zext(1)
        # Extend c by the difference between c's current bit length and n + 1
        n = n + 1 - c.size
        c = c.zext(n)
        res = a + b + c
        return res[0:-1], res[-1]

    def ite(i,t,e):
        return t if i.as_uint() else e

    @binary
    def bvadd(self, other):
        return type(self)(self.as_uint() + other.as_uint())

    @binary
    def bvmul(self, other):
        return type(self)(self.as_uint() * other.as_uint())

    @binary
    def bvudiv(self, other):
        other = other.as_uint()
        if other == 0:
            return type(self)((1 << self.size) - 1)
        return type(self)(self.as_uint() // other)

    @binary
    def bvurem(self, other):
        other = other.as_uint()
        return type(self)(self.as_uint() % other)

    # bvumod

    @binary
    def bvsdiv(self, other):
        other = other.as_sint()
        if other == 0:
            return type(self)((1 << self.size) - 1)
        return type(self)(self.as_sint() // other)

    @binary
    def bvsrem(self, other):
        other = other.as_sint()
        return type(self)(self.as_sint() % other)

    # bvsmod
    def __invert__(self): return self.bvnot()
    def __and__(self, other): return self.bvand(other)
    def __or__(self, other): return self.bvor(other)
    def __xor__(self, other): return self.bvxor(other)

    def __lshift__(self, other): return self.bvshl(other)
    def __rshift__(self, other): return self.bvlshr(other)

    def __neg__(self): return self.bvneg()
    def __add__(self, other): return self.bvadd(other)
    def __sub__(self, other): return self.bvsub(other)
    def __mul__(self, other): return self.bvmul(other)
    def __floordiv__(self, other): return self.bvudiv(other)
    def __mod__(self, other): return self.bvurem(other)

    def __eq__(self, other): return self.bveq(other)
    def __ne__(self, other): return self.bvne(other)
    def __ge__(self, other): return self.bvuge(other)
    def __gt__(self, other): return self.bvugt(other)
    def __le__(self, other): return self.bvule(other)
    def __lt__(self, other): return self.bvult(other)

    def is_x(self):
        return self._value is None

    @no_x
    def as_uint(self):
        return self._value

    @no_x
    def as_sint(self):
        value = self._value
        if (value & (1 << (self.size - 1))):
            value = value - (1 << self.size)
        return value

    as_int = as_sint

    def __int__(self):
        return self.as_uint()

    def __bool__(self):
        return bool(int(self))

    @no_x
    def binary_string(self):
        return "".join(str(int(i)) for i in reversed(self.bits()))

    def as_binary_string(self):
        if self._value is None:
            return "0bX"
        else:
            return "0b" + self.binary_string()

    #@property
    @no_x
    def bits(self):
        return int2seq(self._value, self.size)

    @no_x
    def as_bool_list(self):
        return [bool(x) for x in self._bits]

    @binary
    def repeat(self, other):
        return BitVector[other.as_uint() * self.size]( other.as_uint() * self.bits() )

    @binary_no_cast
    def sext(self, other):
        """
        **NOTE:** Does not cast, returns a raw BitVector instead.

        The user is responsible for handling the conversion. This behavior was
        chosen due to issues with subclassing BitVector (e.g. Bits(n) type
        generator which specializes size). Basically, it's not guaranteed
        that a subtype will respect the __init__ interface, so we return a raw
        BitVector instead and require the user to correctly convert back to the
        subtype.

        Subtypes can improve ergonomics by implementing their own extension
        operators which handle the implicit conversion from raw BitVector.

        TODO: Do this implicit conversion for built-in types like UIntVector.
        """
        ext = other.as_uint()
        return self.concat(BitVector[ext](ext * [self[-1]]), self)

    @binary_no_cast
    def ext(self, other):
        """
        **NOTE:** Does not cast, returns a raw BitVector instead.  See
        docstring for `sext` for more info.
        """
        return self.zext(other)

    @binary_no_cast
    def zext(self, other):
        """
        **NOTE:** Does not cast, returns a raw BitVector instead.  See
        docstring for `sext` for more info.
        """
        ext = other.as_uint()
        return self.concat(BitVector[ext](0), self)

    @staticmethod
    def random(width):
        return BitVector[width](random.randint(0, (1 << width) - 1))




class NumVector(BitVector):
    __hash__ = BitVector.__hash__

class UIntVector(NumVector):
    __hash__ = NumVector.__hash__

    def __repr__(self):
        return "UIntVector[{size}]({value})".format(value=self._value, size=self.size)

    @staticmethod
    def random(width):
        return UIntVector[width](random.randint(0, (1 << width) - 1))



class SIntVector(NumVector):
    __hash__ = NumVector.__hash__

    def __repr__(self):
        return "SIntVector[{size}]({value})".format(value=self._value, size=self.size)

    def __int__(self):
        return self.as_sint()

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


    @staticmethod
    def random(width):
        w = width - 1
        return SIntVector[width](random.randint(-(1 << w), (1 << w) - 1))

    @binary
    def ext(self, other):
        return self.sext(other)

def overflow(a, b, res):
    msb_a = a[-1]
    msb_b = b[-1]
    N = res[-1]
    return (msb_a & msb_b & ~N) or (~msb_a & ~msb_b & N)

