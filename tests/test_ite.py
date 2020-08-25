import random

import pytest

from hwtypes import BitVector
from hwtypes import Bit

ite_params = []
N_TESTS = 32

def rand_bit():
    return Bit(random.randint(0, 1))

for i in range(N_TESTS):
    n = random.randint(1, 32)
    a = BitVector.random(n)
    b = BitVector.random(n)
    c = BitVector.random(1)
    ite_params.append((a, b, c))


for i in range(N_TESTS):
    n = random.randint(1, 32)
    a = BitVector.random(n)
    b = BitVector.random(n)
    c = rand_bit()
    ite_params.append((a, b, c))

@pytest.mark.parametrize("a, b, c", ite_params)
def test_ite(a, b, c):
    res = c.ite(a, b)
    assert res == (a if int(c) else b)

def gen_rand_val(t_idx):
    val = []
    for k in t_idx:
        if k == 0:
            val.append(rand_bit())
        else:
            val.append(BitVector.random(k))
    return tuple(val)

tuple_params = []
for i in range(N_TESTS):
    l = random.randint(1, 8)
    t_idx = [random.randint(0, 4) for _ in range(l)]
    a = gen_rand_val(t_idx)
    b = gen_rand_val(t_idx)
    c = BitVector.random(1)
    tuple_params.append((a, b, c))

for i in range(N_TESTS):
    l = random.randint(1, 8)
    t_idx = [random.randint(0, 4) for _ in range(l)]
    a = gen_rand_val(t_idx)
    b = gen_rand_val(t_idx)
    c = rand_bit()
    tuple_params.append((a, b, c))

@pytest.mark.parametrize("a, b, c", tuple_params)
def test_ite(a, b, c):
    res = c.ite(a, b)
    assert res == (a if int(c) else b)
