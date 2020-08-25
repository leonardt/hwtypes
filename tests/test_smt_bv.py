import pytest
import operator
from hwtypes import SMTBitVector, z3BitVector, SMTBit


WIDTHS = [1,2,4,8]
@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("op", [
    operator.add,
    operator.mul,
    operator.sub,
    operator.floordiv,
    operator.mod,
    operator.and_,
    operator.or_,
    operator.xor,
    operator.lshift,
    operator.rshift,
    ])
@pytest.mark.parametrize("BV", [SMTBitVector, z3BitVector])
def test_bin_op(width, op, BV):
    assert isinstance(op(BV[width](), BV[width]()), BV[width])

@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("op", [
    operator.neg,
    operator.inv,
    ])
@pytest.mark.parametrize("BV", [SMTBitVector, z3BitVector])
def test_unary_op(width, op, BV):
    assert isinstance(op(BV[width]()), BV[width])

@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("op", [
    operator.eq,
    operator.ne,
    operator.lt,
    operator.le,
    operator.gt,
    operator.ge,
    ])
@pytest.mark.parametrize("BV", [SMTBitVector, z3BitVector])
def test_bit_op(width, op, BV):
    assert isinstance(op(BV[width](), BV[width]()), BV.get_family().Bit)

def test_substitute():
    a0 = SMTBitVector[3]()
    a1 = SMTBitVector[3]()
    b0 = SMTBitVector[3]()
    b1 = SMTBitVector[3]()
    expr0 = a0 + b0*a0
    expr1 = expr0.substitute((a0, a1), (b0, b1))
    assert expr1.value is (a1 + b1*a1).value

