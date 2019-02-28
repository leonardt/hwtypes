import pytest
import operator
from hwtypes import UIntVector, Bit

def unsigned(value, width):
    return UIntVector[width](value).as_uint()

NTESTS = 4
WIDTHS = [8]

@pytest.mark.parametrize("op, reference", [
                              (operator.invert, lambda x: ~x),
                              (operator.neg,    lambda x: -x),
                          ])
@pytest.mark.parametrize("width", WIDTHS)
def test_operator_uint1(op, reference, width):
    for _ in range(NTESTS):
        I = UIntVector.random(width)
        expected = unsigned(reference(int(I)), width)
        assert expected == int(op(I))

@pytest.mark.parametrize("op, reference", [
                              (operator.and_,   lambda x, y: x & y ),
                              (operator.or_,    lambda x, y: x | y ),
                              (operator.xor,    lambda x, y: x ^ y ),
                              (operator.lshift, lambda x, y: x << y),
                              (operator.rshift, lambda x, y: x >> y),
                              (operator.add,    lambda x, y: x + y ),
                              (operator.sub,    lambda x, y: x - y ),
                              (operator.mul,    lambda x, y: x * y ),
                              (operator.floordiv,    lambda x, y: x // y if y != 0 else -1),
                          ])
@pytest.mark.parametrize("width", WIDTHS)
def test_operator_uint2(op, reference, width):
    for _ in range(NTESTS):
        I0, I1 = UIntVector.random(width), UIntVector.random(width)
        expected = unsigned(reference(int(I0), int(I1)), width)
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
def test_operator_comparison(op, reference, width):
    for _ in range(NTESTS):
        I0, I1 = UIntVector.random(width), UIntVector.random(width)
        expected = Bit(reference(int(I0), int(I1)))
        assert expected == bool(op(I0, I1))

def test_unsigned():
    a = UIntVector[4](4)
    assert int(a) == 4
