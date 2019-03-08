import pytest
import operator
import random
from itertools import product

from hwtypes import BitVector, Bit

def _rand_bv(width):
    return BitVector[width](random.randint(0, (1 << width) - 1))

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
            with pytest.raises(TypeError):
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
            with pytest.raises(TypeError):
                op(x, y)
        else:
            assert type(x) is type(y)
            res = op(x, y)
            assert type(res) is Bit


@pytest.mark.parametrize("t_constructor", (_rand_bv, _rand_int))
@pytest.mark.parametrize("t_size", (1, 2, 4, 8))
@pytest.mark.parametrize("f_constructor", (_rand_bv, _rand_int))
@pytest.mark.parametrize("f_size", (1, 2, 4, 8))
def test_ite(t_constructor, t_size, f_constructor, f_size):
    pred =  Bit(_rand_int(1))
    t = t_constructor(t_size)
    f = f_constructor(f_size)

    if t_constructor is f_constructor is _rand_bv and t_size == f_size:
        res = pred.ite(t, f)
        assert type(res) is type(t)
    elif t_constructor is f_constructor is _rand_bv:
        with pytest.raises(TypeError):
            res = pred.ite(t, f)
    elif t_constructor is f_constructor: #rand int
        res = pred.ite(t, f)
        t_size = max(t.bit_length(), 1)
        f_size = max(f.bit_length(), 1)
        assert type(res) is BitVector[max(t_size, f_size)]
    elif t_constructor is _rand_bv:
        res = pred.ite(t, f)
        assert type(res) is BitVector[t_size]
    else: #t_constructor is _rand_int
        print(type(t), t, t_constructor, t_size)
        print(type(f), f, f_constructor, f_size)
        res = pred.ite(t, f)
        assert type(res) is BitVector[f_size]
