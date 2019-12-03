import operator
import pytest

from hwtypes import SMTFPVector, RoundingMode, SMTBit

@pytest.mark.parametrize('op', [operator.neg, operator.abs, lambda x : abs(x).fp_sqrt()])
@pytest.mark.parametrize('eb', [4, 16])
@pytest.mark.parametrize('mb', [4, 16])
@pytest.mark.parametrize('mode', [
    RoundingMode.RNE,
    RoundingMode.RNA,
    RoundingMode.RTP,
    RoundingMode.RTN,
    RoundingMode.RTZ,
    ])
@pytest.mark.parametrize('ieee', [False, True])
def test_unary_op(op, eb, mb, mode, ieee):
    T = SMTFPVector[eb, mb, mode, ieee]
    x = T()
    z = op(x)
    assert isinstance(z, T)


@pytest.mark.parametrize('op', [operator.add, operator.sub, operator.mul, operator.truediv])
@pytest.mark.parametrize('eb', [4, 16])
@pytest.mark.parametrize('mb', [4, 16])
@pytest.mark.parametrize('mode', [
    RoundingMode.RNE,
    RoundingMode.RNA,
    RoundingMode.RTP,
    RoundingMode.RTN,
    RoundingMode.RTZ,
    ])
@pytest.mark.parametrize('ieee', [False, True])
def test_bin_ops(op, eb, mb, mode, ieee):
    T = SMTFPVector[eb, mb, mode, ieee]
    x = T()
    y = T()
    z = op(x, y)
    assert isinstance(z, T)

@pytest.mark.parametrize('op', [operator.eq, operator.ne, operator.lt, operator.le, operator.gt, operator.ge])
@pytest.mark.parametrize('eb', [4, 16])
@pytest.mark.parametrize('mb', [4, 16])
@pytest.mark.parametrize('mode', [
    RoundingMode.RNE,
    RoundingMode.RNA,
    RoundingMode.RTP,
    RoundingMode.RTN,
    RoundingMode.RTZ,
    ])
@pytest.mark.parametrize('ieee', [False, True])
def test_bool_ops(op, eb, mb, mode, ieee):
    T = SMTFPVector[eb, mb, mode, ieee]
    x = T()
    y = T()
    z = op(x, y)
    assert isinstance(z, SMTBit)

