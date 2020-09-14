import pytest
import operator
from hwtypes import BitVector, Bit

NTESTS = 4
WIDTHS = [1,2,4,8]

def unsigned(value, width):
    return BitVector[width](value)


def test_illegal():
    with pytest.raises(TypeError):
        BitVector[1](object())

@pytest.mark.parametrize("value, arg",[
    (0, 0),
    (0, [0, 0]),
    (0, Bit(0)),
    (1, Bit(1)),
    (1, [1, 0]),
    (2, [0, 1]),
    (1, 5),
    ])
def test_uint(value, arg):
    assert BitVector[2](arg).as_uint() == value

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
    (operator.add,      lambda x, y: x + y ),
    (operator.mul,      lambda x, y: x * y ),
    (operator.sub,      lambda x, y: x - y ),
    (operator.floordiv, lambda x, y: x // y if y != 0 else -1),
    (operator.mod,      lambda x, y: x % y if y != 0 else x),
    (operator.and_,     lambda x, y: x & y ),
    (operator.or_,      lambda x, y: x | y ),
    (operator.xor,      lambda x, y: x ^ y ),
    (operator.lshift,   lambda x, y: x << y),
    (operator.rshift,   lambda x, y: x >> y),
    ])
@pytest.mark.parametrize("width", WIDTHS)
def test_operator_bit2(op, reference, width):
    for _ in range(NTESTS):
        I0, I1 = BitVector.random(width), BitVector.random(width)
        expected = unsigned(reference(int(I0), int(I1)), width)
        assert expected == int(op(I0, I1))

@pytest.mark.parametrize("op, reference", [
                              (operator.eq, lambda x, y: x == y),
                              (operator.ne, lambda x, y: x != y),
                              (operator.lt, lambda x, y: x  < y),
                              (operator.le, lambda x, y: x <= y),
                              (operator.gt, lambda x, y: x  > y),
                              (operator.ge, lambda x, y: x >= y),
                              ])
@pytest.mark.parametrize("width", WIDTHS)
def test_comparisons(op, reference, width):
    for _ in range(NTESTS):
        I0, I1 = BitVector.random(width), BitVector.random(width)
        expected = Bit(reference(int(I0), int(I1)))
        assert expected == bool(op(I0, I1))

def test_as():
    bv = BitVector[4](1)
    assert bv.as_sint() == 1
    assert bv.as_uint() == 1
    assert int(bv) == 1
    assert bool(bv) == True
    assert bv.bits() == [1,0,0,0]
    assert bv.as_binary_string()== '0b0001'
    assert str(bv) == '1'
    assert repr(bv) == 'BitVector[4](1)'

def test_eq():
    assert BitVector[4](1) == 1
    assert BitVector[4](1) == BitVector[4](1)
    assert [BitVector[4](1)] == [BitVector[4](1)]
    assert [[BitVector[4](1)]] == [[BitVector[4](1)]]


def test_setitem():
  bv = BitVector[3](5)
  assert bv.as_uint() ==5
  bv[0] = 0
  assert repr(bv) == 'BitVector[3](4)'
  bv[1] = 1
  assert repr(bv) == 'BitVector[3](6)'
  bv[2] = 0
  assert repr(bv) == 'BitVector[3](2)'

@pytest.mark.parametrize("val", [
        BitVector.random(8),
        BitVector.random(8).as_sint(),
        BitVector.random(8).as_uint(),
        [0,1,1,0],
    ])
def test_deprecated(val):
    with pytest.warns(DeprecationWarning):
        BitVector(val)

@pytest.mark.parametrize("val", [
        BitVector.random(4),
        BitVector.random(4).as_sint(),
        BitVector.random(4).as_uint(),
        [0,1,1,0],
    ])
def test_old_style(val):
    with pytest.warns(DeprecationWarning):
        with pytest.raises(TypeError):
            BitVector(val, 4)


@pytest.mark.parametrize("op, reference", [
    (operator.floordiv, lambda x, y: x // y if y != 0 else -1),
    (operator.mod,      lambda x, y: x % y if y != 0 else x),
])
def test_operator_by_0(op, reference):
    I0, I1 = BitVector.random(5), 0
    expected = unsigned(reference(int(I0), int(I1)), 5)
    assert expected == int(op(I0, I1))
