from hwtypes import BitVector as BV
import random
import pytest


div_params = [(32, 0xdeadbeaf, 0)]

for i in range(0, 32):
    n = random.randint(1, 32)
    a = random.randint(0, (1 << n) - 1)
    b = random.randint(0, (1 << n) - 1)
    div_params.append((n, a, b))

@pytest.mark.parametrize("n,a,b", div_params)
def test_div(n, a, b):
    if b != 0:
        res = a // b
    else:
        res = (1 << n) - 1

    assert res == (BV[n](a) // BV[n](b)).as_uint()

