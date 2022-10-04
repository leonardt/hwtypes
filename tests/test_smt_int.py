from hwtypes import SMTInt, SMTBitVector, SMTBit
import pysmt.shortcuts as smt
import pytest

def test_sat_unsat():
    x = SMTInt(prefix='x')
    f1 = (x > 0) & (x < 0)
    logic = None
    #Test unsat
    with smt.Solver(logic=logic, name='z3') as solver:
        solver.add_assertion(f1.value)
        res = solver.solve()
        assert not res

    f2 = (x >= 0) & (x*x+x == 30)
    #test sat
    with smt.Solver(logic=logic, name='z3') as solver:
        solver.add_assertion(f2.value)
        res = solver.solve()
        assert res
        x_val = solver.get_value(x.value)
        assert x_val.constant_value() == 5

bin_ops = dict(
    sub = lambda x,y: x-y,
    add = lambda x,y: x+y,
    mul = lambda x,y: x*y,
    div = lambda x,y: x//y,
    lte = lambda x,y: x<=y,
    lt = lambda x,y: x<y,
    gte = lambda x,y: x>=y,
    gt = lambda x,y: x>y,
    eq = lambda x,y: x != y,
    neq = lambda x,y: x == y,
)

unary_ops = dict(
    neg = lambda x: -x,
)

import random

@pytest.mark.parametrize("name, fun", bin_ops.items())
def test_bin_ops(name, fun):
    x = SMTInt(prefix='x')
    y = SMTInt(prefix='y')
    x_val = random.randint(-100, 100)
    y_val = random.choice(list(set(x for x in range(-100,100))-set((0,))))
    f_val = fun(x_val,y_val)
    f = (fun(x, y) == f_val) & (y != 0)
    with smt.Solver(name='z3') as solver:
        solver.add_assertion(f.value)
        res = solver.solve()
        assert res
        x_solved = solver.get_value(x.value).constant_value()
        y_solved = solver.get_value(y.value).constant_value()
        assert fun(x_solved, y_solved) == f_val


@pytest.mark.parametrize("name, fun", unary_ops.items())
def test_unary_ops(name, fun):
    x = SMTInt(prefix='x')
    x_val = random.randint(-100, 100)
    f_val = fun(x_val)
    f = (fun(x) == f_val)
    with smt.Solver(name='z3') as solver:
        solver.add_assertion(f.value)
        res = solver.solve()
        assert res
        x_solved = solver.get_value(x.value).constant_value()
        assert fun(x_solved) == f_val

def test_init_bv():
    SMTInt(SMTBitVector[5]())
    SMTInt(SMTBitVector[5](10))
    SMTInt(SMTBitVector[5](10).value)


def test_as_sint():
    x = SMTBitVector[5](-5)
    x_int = x.as_sint()
    assert isinstance(x_int, SMTInt)
    assert x_int.value.constant_value() == -5

def test_as_uint():
    x = SMTBitVector[5](5)
    x_int = x.as_uint()
    assert isinstance(x_int, SMTInt)
    assert x.as_uint().value.constant_value() == 5

def test_name_table_bug():
    SMTBit(prefix='x')
    SMTInt(prefix='x')

