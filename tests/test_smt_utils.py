from hwtypes import SMTBit
from hwtypes import smt_utils as utils

def _var_idx(v):
    return v._name[2:]

def test_fc():
    x = SMTBit(prefix='x')
    y = SMTBit(prefix='y')
    z = SMTBit(prefix='z')
    XI = _var_idx(x)
    YI = _var_idx(y)
    ZI = _var_idx(z)
    f = utils.Implies(
        utils.And([
            x,
            utils.Or([
                ~y,
                ~z,
            ]),
        ]),
        SMTBit(1)
    )

    f_ht = f.to_hwtypes()
    assert isinstance(f_ht, SMTBit)
    f_str = f.serialize()
    assert f_str == \
'''\
Implies(
|   And(
|   |   x_XI,
|   |   Or(
|   |   |   (! y_YI),
|   |   |   (! z_ZI)
|   |   )
|   ),
|   True
)'''.replace("XI", XI).replace("YI", YI).replace("ZI", ZI)
    f_str = f.serialize(line_prefix='*****', indent='  ')
    assert f_str == \
'''\
*****Implies(
*****  And(
*****    x_XI,
*****    Or(
*****      (! y_YI),
*****      (! z_ZI)
*****    )
*****  ),
*****  True
*****)'''.replace("XI", XI).replace("YI", YI).replace("ZI", ZI)

def test_0_len():
    f = utils.And([])
    assert f.to_hwtypes().value.constant_value() is True
    f = utils.Or([])
    assert f.to_hwtypes().value.constant_value() is False

