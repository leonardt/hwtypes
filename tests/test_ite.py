from bit_vector import BitVector as BV
import random
import pytest


ite_params = []

for i in range(0, 32):
    n = random.randint(1, 32)
    a = BV[n](random.randint(0, (1 << n) - 1))
    b = BV[n](random.randint(0, (1 << n) - 1))
    c = BV[1](random.randint(0, 1))
    ite_params.append((a, b, c))


@pytest.mark.parametrize("a,b,c", ite_params)
def test_ite(a, b, c):
    res = a.ite(b, c)
    assert res == b if int(a) else c
