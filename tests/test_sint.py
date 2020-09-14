import pytest
import operator
import random
from hwtypes import UIntVector, SIntVector, Bit

def signed(value, width):
    return SIntVector[width](value).as_sint()

NTESTS = 4
WIDTHS = [8]

@pytest.mark.parametrize("op, reference", [
                              (operator.invert, lambda x: ~x),
                              (operator.neg,    lambda x: -x),
                          ])
@pytest.mark.parametrize("width", WIDTHS)
def test_operator_int1(op, reference, width):
    for _ in range(NTESTS):
        I = SIntVector.random(width)
        expected = signed(reference(int(I)), width)
        assert expected == int(op(I))

@pytest.mark.parametrize("op, reference", [
                              (operator.and_,   lambda x, y: x & y ),
                              (operator.or_,    lambda x, y: x | y ),
                              (operator.xor,    lambda x, y: x ^ y ),
                              (operator.add,    lambda x, y: x + y ),
                              (operator.sub,    lambda x, y: x - y ),
                              (operator.mul,    lambda x, y: x * y ),
                              (operator.floordiv,    lambda x, y: x // y if y != 0 else -1),
                          ])
@pytest.mark.parametrize("width", WIDTHS)
def test_operator_int2(op, reference, width):
    for _ in range(NTESTS):
        I0, I1 = SIntVector.random(width), SIntVector.random(width)
        expected = signed(reference(int(I0), int(I1)), width)
        assert expected == int(op(I0, I1))

@pytest.mark.parametrize("op, reference", [
                              (operator.eq, lambda x, y: x == y),
                              (operator.ne, lambda x, y: x != y),
                              (operator.lt, lambda x, y: x <  y),
                              (operator.le, lambda x, y: x <= y),
                              (operator.gt, lambda x, y: x >  y),
                              (operator.ge, lambda x, y: x >= y),
                          ])
@pytest.mark.parametrize("width", WIDTHS)
def test_comparison(op, reference, width):
    for _ in range(NTESTS):
        I0, I1 = SIntVector.random(width), SIntVector.random(width)
        if op is operator.floordiv and I1 == 0:
            # Skip divide by zero
            continue
        expected = Bit(reference(int(I0), int(I1)))
        assert expected == bool(op(I0, I1))

@pytest.mark.parametrize("op, reference", [
                              (operator.lshift, lambda x, y: x << y),
                              (operator.rshift, lambda x, y: x >> y),
                          ])
@pytest.mark.parametrize("width", WIDTHS)
def test_operator_int_shift(op, reference, width):
    for _ in range(NTESTS):
        I0, I1 = SIntVector.random(width), UIntVector.random(width)
        expected = signed(reference(int(I0), int(I1)), width)
        assert expected == int(op(I0, I1))

def test_signed():
    a = SIntVector[4](4)
    assert int(a) == 4
    a = SIntVector[4](-4)
    assert a._value != 4, "Stored as unsigned two's complement value"
    assert int(a) == -4, "int returns the native signed int representation"


@pytest.mark.parametrize("op, reference", [
    (operator.floordiv, lambda x, y: x // y if y != 0 else -1),
    (operator.mod,      lambda x, y: x % y if y != 0 else x),
])
def test_operator_by_0(op, reference):
    I0, I1 = SIntVector.random(5), 0
    expected = signed(reference(int(I0), int(I1)), 5)
    assert expected == int(op(I0, I1))
