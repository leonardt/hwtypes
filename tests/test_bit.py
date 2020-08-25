import pytest
import operator
from hwtypes import Bit


class TrueType:
    @staticmethod
    def __bool__():
        return True


class FalseType:
    @staticmethod
    def __bool__():
        return False

def test_illegal():
    with pytest.raises(TypeError):
        Bit(object())

    with pytest.raises(ValueError):
        Bit(2)

@pytest.mark.parametrize("value, arg",[
    (False, False),
    (False, 0),
    (False, FalseType()),
    (False, Bit(0)),
    (True, True),
    (True, 1),
    (True, TrueType()),
    (True, Bit(1)),
    ])
def test_value(value, arg):
    assert bool(Bit(arg)) == value


@pytest.mark.parametrize("op, reference", [
                              (operator.invert, lambda x: not x),
                          ])
@pytest.mark.parametrize("v", [False, True])
def test_operator_bit1(op, reference, v):
    assert reference(v) == bool(op(Bit(v)))



@pytest.mark.parametrize("op, reference", [
                              (operator.and_,   lambda x, y: x & y ),
                              (operator.or_,    lambda x, y: x | y ),
                              (operator.xor,    lambda x, y: x ^ y ),
                              (operator.eq, lambda x, y: x == y),
                              (operator.ne, lambda x, y: x != y),
                          ])
@pytest.mark.parametrize("v1", [False, True])
@pytest.mark.parametrize("v2", [False, True])
def test_operator_bit2(op, reference, v1, v2):
    assert reference(v1, v2) == bool(op(Bit(v1), Bit(v2)))


def test_random():
    assert Bit.random() in [0, 1]
