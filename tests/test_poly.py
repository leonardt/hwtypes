import pytest

from pysmt import shortcuts as sc

from hwtypes import BitVector, SIntVector, UIntVector
from hwtypes import Bit

from hwtypes import SMTBit, SMTBitVector
from hwtypes import SMTUIntVector, SMTSIntVector

@pytest.mark.parametrize("cond_0", [Bit(0), Bit(1)])
@pytest.mark.parametrize("cond_1", [Bit(0), Bit(1)])
def test_poly_bv(cond_0, cond_1):
    S = SIntVector[8]
    U = UIntVector[8]
    val = cond_0.ite(S(0), U(0)) - 1

    assert val < 0 if cond_0 else val > 0
    val2 = cond_1.ite(S(-1), val)
    val2 = val2.ext(1)
    assert val2 == val.sext(1) if cond_0 or cond_1 else val2 == val.zext(1)

    val3 = cond_1.ite(cond_0.ite(U(0), S(1)), cond_0.ite(S(-1), U(2)))

    if cond_1:
        if cond_0:
            assert val3 == 0
            assert val3 - 1 > 0
        else:
            assert val3 == 1
            assert val3 - 2 < 0
    else:
        if cond_0:
            assert val3 == -1
            assert val3 < 0
        else:
            assert val3 == 2
            assert val3 - 3 > 0

def test_poly_smt():
    S = SMTSIntVector[8]
    U = SMTUIntVector[8]

    c1 = SMTBit(name='c1')
    u1 = U(name='u1')
    u2 = U(name='u2')
    s1 = S(name='s1')
    s2 = S(name='s2')

    # NOTE: __eq__ on pysmt terms is strict structural equivalence
    # for example:
    assert u1.value == u1.value  # .value extract pysmt term
    assert u1.value != u2.value
    assert (u1 * 2).value != (u1 + u1).value
    assert (u1 + u2).value == (u1 + u2).value
    assert (u1 + u2).value != (u2 + u1).value

    # On to the real test
    expr = c1.ite(u1, s1) < 1
    # get the pysmt values
    _c1, _u1, _s1 = c1.value, u1.value, s1.value
    e1 = sc.Ite(_c1, _u1, _s1)
    one = sc.BV(1, 8)
    # Here we see that `< 1` dispatches symbolically
    f = sc.Ite(_c1, sc.BVULT(e1, one), sc.BVSLT(e1, one))
    assert expr.value == f

    expr = expr.ite(c1.ite(u1, s1), c1.ite(s2, u2)).ext(1)

    e2 = sc.Ite(_c1, s2.value, u2.value)
    e3 = sc.Ite(f, e1, e2)

    se = sc.BVSExt(e3, 1)
    ze = sc.BVZExt(e3, 1)


    g = sc.Ite(
        f,
        sc.Ite(_c1, ze, se),
        sc.Ite(_c1, se, ze)
     )
    # Here we see that ext dispatches symbolically / recursively
    assert expr.value == g


    # Here we see that polymorphic types only build muxes if they need to
    expr = c1.ite(u1, s1) + 1
    assert expr.value == sc.BVAdd(e1, one)
    # Note how it is not:
    assert expr.value != sc.Ite(_c1, sc.BVAdd(e1, one), sc.BVAdd(e1, one))
    # which was the pattern for sign dependent operators

