from hwtypes import SIntVector as SV
from hwtypes import overflow
import random
import pytest


ovfl_params = []

for i in range(0, 32):
    n = random.randint(1, 32)
    a = SV[n](random.randint(-(1 << (n - 1)), (1 << (n - 1)) - 1))
    b = SV[n](random.randint(-(1 << (n - 1)), (1 << (n - 1)) - 1))
    ovfl_params.append((a, b))


@pytest.mark.parametrize("a,b", ovfl_params)
def test_ovfl(a, b):
    expected = ((a < 0) and (b < 0) and ((a + b) >= 0)) or \
               ((a >= 0) and (b >= 0) and ((a + b) < 0))
    assert overflow(a, b, a + b) == expected
