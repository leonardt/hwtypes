from __future__ import division
from .compatibility import IntegerTypes, StringTypes
import numpy as np

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


def type_check_and_promote_ints(fn):
    def wrapped(self, other):
        if not (isinstance(other, BitVector) or isinstance(other, int) and other.bit_length() <= self.num_bits):
            raise TypeError(fn, other)
        if isinstance(other, int):
            other = BitVector(other, self.num_bits)
        return fn(self, other)
    return wrapped

# For many operations only support use of X values if both operands are X
def handle_both_x(fn):
    def wrapped(self, other):
        if isinstance(other, BitVector):
            if self._value is None and other._value is None:
                return BitVector(None, num_bits=self.num_bits, signed=self.signed)
            elif self._value is None or other._value is None:
                raise Exception("Invalid use of X value")
        elif self._value is None:
            raise Exception("Invalid use of X value")
        return fn(self, other)

    return wrapped

def no_x_support(fn):
    def wrapped(self):
        if self._value is None:
            raise Exception("Invalid use of X value")
        return fn(self)

    return wrapped

class BitVector:
    def __init__(self, value=0, num_bits=None, signed=None):
        if isinstance(value, BitVector):
            self._value = value._value
            if signed is None:
                self.signed = value.signed
            else:
                self.signed = signed
            if num_bits is None:
                num_bits = value.num_bits
            self._bits = int2seq(self._value, num_bits)
        elif isinstance(value, IntegerTypes):
            if num_bits is None:
                num_bits = max(value.bit_length(), 1)
            if signed is False and value < 0:
                raise ValueError()
            elif value >= 0:
                self.signed = False if signed is None else signed
            else:
                value = value + (1 << num_bits)
                self.signed = True
            self._value = value
            self._bits = int2seq(value, num_bits)
        elif isinstance(value, list):
            self.signed = signed
            if not (all(x == 0 or x == 1 for x in value) or all(x == False or x == True for x in value)):
                raise Exception("BitVector list initialization must be a list of 0s and 1s or a list of True and False")
            if num_bits is None:
                num_bits = len(value)
            self._value = seq2int(value)
            self._bits = value
            if self.signed and self._bits[-1]:
                self._value -= (1 << num_bits)
        elif value is None:
            self._value = None
            self._bits = None
            if num_bits == 0:
                raise Exception("X valued BitVector requires an explicit width")
        else:
            raise Exception("BitVector initialization with type {} not supported".format(type(value)))
        self.num_bits = num_bits
        if self._value is not None and self._value.bit_length() > self.num_bits:
            raise Exception("BitVector initialized with too small a width")

    @type_check_and_promote_ints
    @handle_both_x
    def __and__(self, other):
        assert isinstance(other, BitVector)
        return BitVector(self._value & other._value, num_bits=self.num_bits, signed=self.signed)

    @type_check_and_promote_ints
    def __rand__(self, other):
        return self.__and__(other);

    def __or__(self, other):
        assert isinstance(other, BitVector)
        if self._value is None and other._value is None:
            return BitVector(None, num_bits=self.num_bits, signed=self.signed)
        elif self._value is True or other._value is True: # Handle one X
            return BitVector(True, num_bits=self.num_bits, signed=self.signed)
        elif self._value is None or other._value is None:
            raise Exception("Invalid use of X value")
        else:
            return BitVector(self._value | other._value, num_bits=self.num_bits, signed=self.signed)

    @handle_both_x
    def __xor__(self, other):
        assert isinstance(other, BitVector)
        return BitVector(self._value ^ other._value, num_bits=self.num_bits, signed=self.signed)

    @handle_both_x
    def __lshift__(self, other):
        if isinstance(other, int):
            if other < 0:
                raise ValueError("Cannot shift by negative value {}".format(other))
            shift_result = self._value << other
        else:
            assert isinstance(other, BitVector)
            if other.as_int() < 0:
                raise ValueError("Cannot shift by negative value {}".format(other))
            shift_result = self._value << other._value
        mask = (1 << self.num_bits) - 1
        return BitVector(shift_result & mask, num_bits=self.num_bits, signed=self.signed)

    @handle_both_x
    def __rshift__(self, other):
        """
        numpy.right_shift is a logical right shift, Python defaults to arithmetic
        .item() returns a python type
        """
        if isinstance(other, int):
            if other < 0:
                raise ValueError("Cannot shift by negative value {}".format(other))
            shift_result = self._value >> other
            mask = (1 << max((self.num_bits - other), 0)) - 1
        else:
            assert isinstance(other, BitVector)
            if other.as_int() < 0:
                raise ValueError("Cannot shift by negative value {}".format(other))
            shift_result = self._value >> other._value
            mask = (1 << max((self.num_bits - other._value), 0)) - 1
        return BitVector(shift_result & mask, num_bits=self.num_bits, signed=self.signed)

    @handle_both_x
    def arithmetic_shift_right(self, other):
        if isinstance(other, int):
            if other < 0:
                raise ValueError("Cannot shift by negative value {}".format(other))
            shift_result = self._value >> other
        else:
            assert isinstance(other, BitVector)
            if other.as_int() < 0:
                raise ValueError("Cannot shift by negative value {}".format(other))
            shift_result = self._value >> other._value
        mask = (1 << self.num_bits) - 1
        return BitVector(shift_result & mask, num_bits=self.num_bits, signed=self.signed)

    @type_check_and_promote_ints
    @handle_both_x
    def __add__(self, other):
        assert isinstance(other, BitVector)
        result = self._value + other._value
        mask = (1 << self.num_bits) - 1
        return BitVector(result & mask, num_bits=self.num_bits, signed=self.signed)

    @type_check_and_promote_ints
    @handle_both_x
    def __sub__(self, other):
        assert isinstance(other, BitVector)
        result = self._value - other._value
        mask = (1 << self.num_bits) - 1
        return BitVector(result & mask, num_bits=self.num_bits, signed=self.signed)

    @handle_both_x
    def __mul__(self, other):
        assert isinstance(other, BitVector)
        result = self.as_int() * other.as_int()
        if result < 0:
            result += (1 << (self.num_bits * 2))
        mask = (1 << (self.num_bits * 2)) - 1
        return BitVector(result & mask, num_bits=self.num_bits * 2, signed=self.signed)

    @handle_both_x
    def __div__(self, other):
        assert isinstance(other, BitVector)
        if self.signed:
            result = (~self + 1)._value // (~other + 1)._value
            our_sign = self._value >> self.num_bits & 1
            their_sign = other._value >> other.num_bits & 1
            if our_sign ^ their_sign:
                result = -result
            print(result)
            return BitVector(result, num_bits=self.num_bits, signed=self.signed)
        else:
            result = self._value // other._value
            mask = (1 << self.num_bits) - 1
            return BitVector(result & mask, num_bits=self.num_bits, signed=self.signed)

    __floordiv__ = __div__
    __truediv__ = __div__

    @type_check_and_promote_ints
    @handle_both_x
    def __lt__(self, other):
        return BitVector(int(self.as_int() < other.as_int()), num_bits=1)

    @type_check_and_promote_ints
    @handle_both_x
    def __le__(self, other):
        return BitVector(int(self.as_int() <= other.as_int()), num_bits=1)

    @type_check_and_promote_ints
    @handle_both_x
    def __gt__(self, other):
        return BitVector(int(self.as_int() > other.as_int()), num_bits=1)

    @type_check_and_promote_ints
    @handle_both_x
    def __ge__(self, other):
        return BitVector(int(self.as_int() >= other.as_int()), num_bits=1)

    @no_x_support
    def as_int(self):
        if self.signed:
            value = self._value
            if (value & (1 << (self.num_bits - 1))):
                value = value - (1 << self.num_bits)
            return value
        else:
            return self._value


    def __int__(self):
        return self.as_int()

    def as_binary_string(self):
        if self._value is None:
            return "0bX"
        else:
            return "0b" + np.binary_repr(self.as_int(), self.num_bits)

    @no_x_support
    def as_bool_list(self):
        return [bool(x) for x in self._bits]

    @property
    @no_x_support
    def bits(self):
        return int2seq(self._value)

    @no_x_support
    def bit_string(self):
        return "".join(str(int(i)) for i in reversed(self.bits()))

    # @no_x_support
    def __getitem__(self, index):
        if isinstance(index, slice):
            return BitVector(self._bits[index])
        else:
            return self.bits()[index]

    # @no_x_support
    def __setitem__(self, index, value):
        if isinstance(index, slice):
            raise NotImplementedError()
        else:
            if not (isinstance(value, bool) or isinstance(value, int) and value in {0, 1}):
                raise ValueError("Second argument __setitem__ on a single BitVector index should be a boolean or 0 or 1, not {value}".format(value=value))
            self._bits[index] = value

    def __len__(self):
        return self.num_bits

    def __str__(self):
        if self._value is None:
            return "X"
        else:
            return str(self._value)

    def __repr__(self):
        return "BitVector({0}, {1})".format(str(self), self.num_bits)

    def __invert__(self):
        if self._value is None:
            return BitVector(None, num_bits=self.num_bits, signed=self.signed)
        else:
            return BitVector(~self._value + (1<<self.num_bits), num_bits=self.num_bits, signed=self.signed)

    def __eq__(self, other):
        if isinstance(other, BitVector):
            return BitVector(self._value == other._value, num_bits=1)
        elif isinstance(other, list) and all(isinstance(x, bool) for x in other):
            return self.as_bool_list() == other
        elif isinstance(other, bool) and self.num_bits == 1:
            return self.as_bool_list()[0] == other
        elif isinstance(other, int):
            return self.as_int() == other
        raise NotImplementedError(type(other))

    @no_x_support
    def __neg__(self):
        if not self.signed:
            raise TypeError("Cannot call __neg__ on unsigned BitVector")
        return BitVector(~self._value + 1, num_bits=self.num_bits, signed=True)

    def __bool__(self):
        return bool(self.as_int())

    def bits(self):
        return self.as_bool_list()

    @property
    def unsigned_value(self):
        return self._value

    # Note: In concat(x, y), the MSB of the result is the MSB of x.
    @staticmethod
    def concat(x, y):
        bits = y.bits()
        bits.extend(x.bits())
        return BitVector(bits)
