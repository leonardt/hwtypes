from hwtypes import SMTBit
from hwtypes import smt_utils as utils

def test_fc():
    x = SMTBit(prefix='x')
    y = SMTBit(prefix='y')
    z = SMTBit(prefix='z')
    f = utils.Implies(
        utils.And([
            x & y,
            utils.Or([
                ~y & z,
                ~z & x,
            ]),
        ]),
        SMTBit(1)
    )

    f_ht = f.to_hwtypes()
    assert isinstance(f_ht, SMTBit)
    f_str = f.serialize()
    assert isinstance(f_str, str)


def test_0_len():
    f = utils.And([])
    assert f.to_hwtypes().value.constant_value() == True
    f = utils.Or([])
    assert f.to_hwtypes().value.constant_value() == False
