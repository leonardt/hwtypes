import pytest
import operator
from hwtypes import SMTBit, SMTBitVector, z3Bit

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


def test_ite_tuple():
    a = SMTBitVector[8](), SMTBit(), SMTBitVector[4]()
    b = SMTBitVector[8](), SMTBit(), SMTBitVector[4]()
    c = SMTBit()

    res = c.ite(a, b)
    assert isinstance(res, tuple)
    assert len(res) == 3
    assert isinstance(res[0], SMTBitVector[8])
    assert isinstance(res[1], SMTBit)
    assert isinstance(res[2], SMTBitVector[4])


def test_ite_fail():
    p = SMTBit()
    t = SMTBit()
    f = SMTBitVector[1]()
    with pytest.raises(TypeError):
        res = p.ite(t, f)


def test_bool():
    b = SMTBit()
    with pytest.raises(TypeError):
        bool(b)
