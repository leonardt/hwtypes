from bit_vector import BitVector as BV
import random
import pytest


ite_params = []

for i in range(0, 32):
    n = random.randint(1, 32)
    a = BV(random.randint(0, (1 << n) - 1), n)
    b = BV(random.randint(0, (1 << n) - 1), n)
    c = BV(random.randint(0, 1), 1)
    ite_params.append((a, b, c))


@pytest.mark.parametrize("a,b,c", ite_params)
def test_ite(a, b, c):
    res = a.ite(b, c)
    assert res == b if int(a) else c
