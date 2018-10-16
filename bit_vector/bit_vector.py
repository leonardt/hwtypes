from .compatibility import IntegerTypes, StringTypes
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
    def wrapped(self):
        # cast type
        T = type(self)
        val =  fn(self)
        return val if val.num_bits == 1 else T(val)

    return wrapped

def binary_no_cast(fn):
    def wrapped(self, other):
        # promote bool and int
        if isinstance(other, (int, bool)):
            other = BitVector(other, self.num_bits)

        # type check
        if not (isinstance(other, BitVector) or isinstance(other, int) and other.bit_length() <= self.num_bits):
            raise TypeError(fn, other)

        # handle binary x
        if isinstance(other, BitVector):
            if self._value is None and other._value is None:
                #return BitVector(None, num_bits=self.num_bits)
                return BitVector(1, num_bits=self.num_bits)
            elif self._value is None or other._value is None:
                raise Exception("Invalid use of X value")
        elif self._value is None:
            raise Exception("Invalid use of X value")

        return fn(self, other)
    return wrapped

def binary(fn):
    def wrapped(self, other):
        # promote bool and int
        if isinstance(other, (int, bool)):
            other = BitVector(other, self.num_bits)

        # type check
        if not (isinstance(other, BitVector) or isinstance(other, int) and other.bit_length() <= self.num_bits):
            raise TypeError(fn, other)

        # handle binary x
        if isinstance(other, BitVector):
            if self._value is None and other._value is None:
                return BitVector(None, num_bits=self.num_bits)
            elif self._value is None or other._value is None:
                raise Exception("Invalid use of X value")
        elif self._value is None:
            raise Exception("Invalid use of X value")

        # cast type
        T = type(self)
        val =  fn(self, other)
        return val if val.num_bits == 1 else T(val)

    return wrapped

def no_x(fn):
    def wrapped(self, *args, **kwargs):
        if self._value is None:
            raise Exception("Invalid use of X value")
        return fn(self, *args, **kwargs)

    return wrapped

class BitVector:
    def __init__(self, value=0, num_bits=None):
        if isinstance(value, BitVector):
            if num_bits is None:
                num_bits = value.num_bits
            self._value = value._value
            self._bits = int2seq(self._value, num_bits)
        elif isinstance(value, IntegerTypes):
            if num_bits is None:
                num_bits = max(value.bit_length(), 1)
            self._value = value
            self._value &= (1 << num_bits)-1
            self._bits = int2seq(value, num_bits)
        elif isinstance(value, list):
            if not (all(x == 0 or x == 1 for x in value) or all(x == False or x == True for x in value)):
                raise Exception("BitVector list initialization must be a list of 0s and 1s or a list of True and False")
            if num_bits is None:
                num_bits = len(value)
            self._value = seq2int(value)
            self._bits = value
        elif value is None:
            if num_bits is None:
                raise Exception("X valued BitVector requires an explicit width")
            self._value = None
            self._bits = None
        else:
            raise Exception("BitVector initialization with type {} not supported".format(type(value)))

        self.num_bits = num_bits
        if self._value is not None and self._value.bit_length() > self.num_bits:
            raise Exception("BitVector initialized with too small a width")


    def __hash__(self):
        return hash(repr(self))

    def __str__(self):
        if self._value is None:
            return "X"
        else:
            return str(int(self))

    def __repr__(self):
        return "BitVector({value}, {num_bits})".format(value=self._value, num_bits=self.num_bits)

    @no_x
    def __setitem__(self, index, value):
        if isinstance(index, slice):
            raise NotImplementedError()
        else:
            if not (isinstance(value, bool) or isinstance(value, int) and value in {0, 1}):
                raise ValueError("Second argument __setitem__ on a single BitVector index should be a boolean or 0 or 1, not {value}".format(value=value))
            self._bits[index] = value

    @no_x
    def __getitem__(self, index):
        if isinstance(index, slice):
            return BitVector(self._bits[index])
        else:
            return self.bits()[index]

    def __len__(self):
        return self.num_bits

    # Note: In concat(x, y), the MSB of the result is the MSB of x.
    @staticmethod
    def concat(x, y):
        bits = y.bits()
        bits.extend(x.bits())
        return BitVector(bits)

    @unary
    def bvnot(self):
        if self._value is None:
            return BitVector(None, num_bits=self.num_bits)
        else:
            return BitVector(~self.as_uint(), num_bits=self.num_bits)

    @binary
    def bvand(self, other):
        return BitVector(self.as_uint() & other.as_uint(), num_bits=self.num_bits)

    @binary
    def bvnand(self, other):
        return not self.bvand(other)


    @binary
    def bvor(self, other):
        return BitVector(self.as_uint() | other.as_uint(), num_bits=self.num_bits)

    @binary
    def bvnor(self, other):
        return not self.bvor(other)


    @binary
    def bvxor(self, other):
        return BitVector(self.as_uint() ^ other.as_uint(), num_bits=self.num_bits)

    @binary
    def bvxnor(self, other):
        return not self.bvxor(other)



    @binary
    def bvshl(self, other):
        return BitVector( self.as_uint() << other.as_uint(), num_bits=self.num_bits)

    @binary
    def bvlshr(self, other):
        return BitVector( self.as_uint() >> other.as_uint(), num_bits=self.num_bits)

    @binary
    def bvashr(self, other):
        return BitVector( self.as_sint() >> other.as_uint(), num_bits=self.num_bits)

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
            other = BitVector(list)

        #if self.is_x() and isinstance(other, BitVector) or \
        #        isinstance(other, list) and \
        #        all(isinstance(x, bool) for x in other):
        #    result = True
        #elif isinstance(other, list) and all(isinstance(x, bool) for x in other):
        #    result = self.as_bool_list() == other
        #elif isinstance(other, bool) and self.num_bits == 1:
        #    result = self.as_bool_list()[0] == other
        return BitVector( self._value == other._value, 1 )

    bveq = bvcomp

    @binary_no_cast
    def bvne(self, other):
        return BitVector(self.as_uint() != other.as_uint(), num_bits=1)

    @binary_no_cast
    def bvult(self, other):
        return BitVector(self.as_uint() < other.as_uint(), num_bits=1)

    @binary_no_cast
    def bvule(self, other):
        return BitVector(self.as_uint() <= other.as_uint(), num_bits=1)

    @binary_no_cast
    def bvugt(self, other):
        return BitVector(self.as_uint() > other.as_uint(), num_bits=1)

    @binary_no_cast
    def bvuge(self, other):
        return BitVector(self.as_uint() >= other.as_uint(), num_bits=1)

    @binary_no_cast
    def bvslt(self, other):
        return BitVector(self.as_sint() < other.as_sint(), num_bits=1)

    @binary_no_cast
    def bvsle(self, other):
        return BitVector(self.as_sint() <= other.as_sint(), num_bits=1)

    @binary_no_cast
    def bvsgt(self, other):
        return BitVector(self.as_sint() > other.as_sint(), num_bits=1)

    @binary
    def bvsge(self, other):
        return BitVector(self.as_sint() >= other.as_sint(), num_bits=1)

    @unary
    def bvneg(self):
        if self._value is None:
            return BitVector(None, num_bits=self.num_bits)
        else:
            return BitVector(~self.as_uint()+1, num_bits=self.num_bits)

    @binary
    def bvadd(self, other):
        return BitVector(self.as_uint() + other.as_uint(), num_bits=self.num_bits)
    @binary
    def bvsub(self, other):
        return self.bvadd(other.bvneg())

    @binary
    def bvmul(self, other):
        return BitVector(self.as_uint() * other.as_uint(), num_bits=self.num_bits)

    @binary
    def bvudiv(self, other):
        other = other.as_uint()
        if other == 0:
            return BitVector(1, num_bits=self.num_bits)
        return BitVector(self.as_uint() // other, num_bits=self.num_bits)

    @binary
    def bvurem(self, other):
        other = other.as_uint()
        if other == 0:
            return self
        return BitVector(self.as_uint() % other, num_bits=self.num_bits)

    # bvumod

    @binary
    def bvsdiv(self, other):
        other = other.as_sint()
        if other == 0:
            return BitVector(1, num_bits=self.num_bits)
        return BitVector(self.as_sint() // other, num_bits=self.num_bits)

    @binary
    def bvsrem(self, other):
        other = other.as_sint()
        if other == 0:
            return self
        return BitVector(selfsas_sint() % other, num_bits=self.num_bits)

    # bvsmod



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

    def is_x(self):
        return self._value is None

    @no_x
    def as_uint(self):
        return self._value

    @no_x
    def as_sint(self):
        value = self._value
        if (value & (1 << (self.num_bits - 1))):
            value = value - (1 << self.num_bits)
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
        return int2seq(self._value, self.num_bits)

    @no_x
    def as_bool_list(self):
        return [bool(x) for x in self._bits]




    @binary
    def repeat(self, other):
        return BitVector( other.as_uint() * self.bits() )

    @binary
    def sext(self, other):
        return self.concat(BitVector(other.as_uint() * [self[-1]]), self)

    @binary
    def ext(self, other):
        return self.zext(other)

    @binary
    def zext(self, other):
        return self.concat(BitVector(other.as_uint() * [0]), self)

    @staticmethod
    def random(width):
        return BitVector(random.randint(0, (1 << width) - 1), width)




class NumVector(BitVector):
    __hash__ = BitVector.__hash__

class UIntVector(NumVector):
    __hash__ = NumVector.__hash__

    def __repr__(self):
        return "UIntVector({value}, {num_bits})".format(value=self._value, num_bits=self.num_bits)

    @staticmethod
    def random(width):
        return UIntVector(random.randint(0, (1 << width) - 1), width)



class SIntVector(NumVector):
    __hash__ = NumVector.__hash__

    def __repr__(self):
        return "SIntVector({value}, {num_bits})".format(value=self._value, num_bits=self.num_bits)

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
        return SIntVector(random.randint(-(1 << w), (1 << w) - 1), width)

    @binary
    def ext(self, other):
        return self.sext(other)

