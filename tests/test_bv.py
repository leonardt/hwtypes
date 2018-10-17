import pytest
import operator
from bit_vector import BitVector

NTESTS = 4
WIDTHS = [1,2,4,8]

def unsigned(value, width):
    return BitVector(value, width)

@pytest.mark.parametrize("op, reference", [
                              (operator.invert, lambda x: ~x),
                          ])
@pytest.mark.parametrize("width", WIDTHS)
def test_operator_bit1(op, reference, width):
    for _ in range(NTESTS):
        I = BitVector.random(width)
        expected = unsigned(reference(int(I)), width)
        assert expected == int(op(I))

@pytest.mark.parametrize("op, reference", [
                              (operator.eq, lambda x, y: x == y),
                              (operator.ne, lambda x, y: x != y),
                              (operator.and_,   lambda x, y: x & y ),
                              (operator.or_,    lambda x, y: x | y ),
                              (operator.xor,    lambda x, y: x ^ y ),
                              (operator.lshift, lambda x, y: x << y),
                              (operator.rshift, lambda x, y: x >> y),
                          ])
@pytest.mark.parametrize("width", WIDTHS)
def test_operator_bit2(op, reference, width):
    for _ in range(NTESTS):
        I0, I1 = BitVector.random(width), BitVector.random(width)
        expected = unsigned(reference(int(I0), int(I1)), width)
        assert expected == int(op(I0, I1))

def test_as():
    bv = BitVector(1,4)
    assert bv.as_sint() == 1
    assert bv.as_uint() == 1
    assert int(bv) == 1
    assert bool(bv) == True
    assert bv.bits() == [1,0,0,0]
    assert bv.as_binary_string()== '0b0001'
    assert str(bv) == '1'
    assert repr(bv) == 'BitVector(1, 4)'

def test_eq():
    assert BitVector(1,4) == 1
    assert BitVector(1,4) == BitVector(1,4)
    assert [BitVector(1,4)] == [BitVector(1,4)]
    assert [[BitVector(1,4)]] == [[BitVector(1,4)]]

    assert BitVector(None,1) == BitVector(None,1) 

def test_setitem():
  bv = BitVector(5)
  assert bv.as_uint() ==5
  bv[0] = 0
  assert repr(bv) == 'BitVector(4, 3)'
  bv[1] = 1
  assert repr(bv) == 'BitVector(6, 3)'
  bv[2] = 0
  assert repr(bv) == 'BitVector(2, 3)'
