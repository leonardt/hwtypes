from hwtypes import BitVector as BV
import random
import pytest


adc_params = []

for i in range(0, 32):
    n = random.randint(1, 32)
    a = BV[n](random.randint(0, (1 << n) - 1))
    b = BV[n](random.randint(0, (1 << n) - 1))
    c = BV[1](random.randint(0, 1))
    adc_params.append((a, b, c))


@pytest.mark.parametrize("a,b,c", adc_params)
def test_adc(a, b, c):
    res, carry = a.adc(b, c)
    assert res == a + b + c.zext(a.size - c.size)
    assert carry == (a.zext(1) + b.zext(1) + c.zext(1 + a.size - c.size))[-1]

def test_adc1():
    a = BV[16](27734)
    b = BV[16](13207)
    c = BV[1](0)
    res, carry = a.adc(b, c)
    assert res == a + b + c.zext(a.size - c.size)
    assert carry == (a.zext(1) + b.zext(1) + c.zext(1 + a.size - c.size))[-1]
