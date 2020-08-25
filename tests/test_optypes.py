import pytest
import operator
import random
from itertools import product

from hwtypes import SIntVector, BitVector, Bit
from hwtypes.bit_vector_abc import InconsistentSizeError
from hwtypes.bit_vector_util import PolyVector, PolyBase

def _rand_bv(width):
    return BitVector[width](random.randint(0, (1 << width) - 1))

def _rand_signed(width):
    return SIntVector[width](random.randint(0, (1 << width) - 1))


def _rand_int(width):
    return random.randint(0, (1 << width) - 1)

@pytest.mark.parametrize("op", [
                              operator.and_,
                              operator.or_,
                              operator.xor,
                              operator.lshift,
                              operator.rshift,
                          ])
@pytest.mark.parametrize("width1", (1, 2))
@pytest.mark.parametrize("width2", (1, 2))
@pytest.mark.parametrize("use_int", (False, True))
def test_bin(op, width1, width2, use_int):
    x = _rand_bv(width1)
    if use_int:
        y = _rand_int(width2)
        res = op(x, y)
        assert type(res) is type(x)
    else:
        y = _rand_bv(width2)
        if width1 != width2:
            assert type(x) is not type(y)
            with pytest.raises(InconsistentSizeError):
                op(x, y)
        else:
            assert type(x) is type(y)
            res = op(x, y)
            assert type(res) is type(x)


@pytest.mark.parametrize("op", [
                              operator.eq,
                              operator.ne,
                              operator.lt,
                              operator.le,
                              operator.gt,
                              operator.ge,
                              ])
@pytest.mark.parametrize("width1", (1, 2))
@pytest.mark.parametrize("width2", (1, 2))
@pytest.mark.parametrize("use_int", (False, True))
def test_comp(op, width1, width2, use_int):
    x = _rand_bv(width1)
    if use_int:
        y = _rand_int(width2)
        res = op(x, y)
        assert type(res) is Bit
    else:
        y = _rand_bv(width2)
        if width1 != width2:
            assert type(x) is not type(y)
            with pytest.raises(InconsistentSizeError):
                op(x, y)
        else:
            assert type(x) is type(y)
            res = op(x, y)
            assert type(res) is Bit


@pytest.mark.parametrize("t_constructor", (_rand_bv, _rand_signed, _rand_int))
@pytest.mark.parametrize("t_size", (1, 2, 4))
@pytest.mark.parametrize("f_constructor", (_rand_bv, _rand_signed, _rand_int))
@pytest.mark.parametrize("f_size", (1, 2, 4))
def test_ite(t_constructor, t_size, f_constructor, f_size):
    pred =  Bit(_rand_int(1))
    t = t_constructor(t_size)
    f = f_constructor(f_size)

    t_is_bv_constructor = t_constructor in {_rand_signed, _rand_bv}
    f_is_bv_constructor = f_constructor in {_rand_signed, _rand_bv}
    sizes_equal = t_size == f_size

    if (t_constructor is f_constructor and t_is_bv_constructor and sizes_equal):
        # The same bv_constructor
        res = pred.ite(t, f)
        assert type(res) is type(t)
    elif t_is_bv_constructor and f_is_bv_constructor and sizes_equal:
        # Different bv_constuctor
        res = pred.ite(t, f)
        # The bases should be the most specific types that are common
        # to both branches and PolyBase.
        assert isinstance(res, PolyBase)
        assert isinstance(res, BitVector[t_size])
    elif t_is_bv_constructor and f_is_bv_constructor and not sizes_equal:
        # BV with different size
        with pytest.raises(InconsistentSizeError):
            res = pred.ite(t, f)
    else:
        # Trying to coerce an int
        with pytest.raises(TypeError):
            res = pred.ite(t, f)
