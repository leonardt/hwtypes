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
