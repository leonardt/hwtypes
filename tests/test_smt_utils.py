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
    print(f_str)
    assert f_str == \
'''\
Implies(
|   And(
|   |   (x_0 & y_0),
|   |   Or(
|   |   |   ((! y_0) & z_0),
|   |   |   ((! z_0) & x_0)
|   |   )
|   ),
|   True
)'''


def test_0_len():
    f = utils.And([])
    assert f.to_hwtypes().value.constant_value() is True
    f = utils.Or([])
    assert f.to_hwtypes().value.constant_value() is False

