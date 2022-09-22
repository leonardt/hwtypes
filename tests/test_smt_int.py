
from hwtypes import SMTInt
import pysmt.shortcuts as smt
from pysmt.typing import INT

def test_ops():
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