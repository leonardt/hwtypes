import pytest
import operator
from hwtypes import SMTBit, z3Bit

@pytest.mark.parametrize("op", [
    operator.and_,
    operator.or_,
    operator.xor,
    operator.eq,
    operator.ne,
    ])
@pytest.mark.parametrize("Bit", [SMTBit, z3Bit])
def test_bin_op(op, Bit):
    assert isinstance(op(Bit(), Bit()), Bit)

@pytest.mark.parametrize("op", [
    operator.inv,
    ])
@pytest.mark.parametrize("Bit", [SMTBit, z3Bit])
def test_unary_op(op, Bit):
    assert isinstance(op(Bit()), Bit)

def test_substitute():
    a0 = SMTBit()
    a1 = SMTBit()
    b0 = SMTBit()
    b1 = SMTBit()
    expr0 = a0|b0
    expr1 = expr0.substitute((a0, a1), (b0, b1))
    assert expr1.value is (a1|b1).value


