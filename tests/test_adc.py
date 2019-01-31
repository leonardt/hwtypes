from bit_vector import BitVector as BV
import random
import pytest


adc_params = []

for i in range(0, 32):
    n = random.randint(1, 32)
    a = BV(random.randint(0, (1 << n) - 1), n)
    b = BV(random.randint(0, (1 << n) - 1), n)
    c = BV(random.randint(0, 1), 1)
    adc_params.append((a, b, c))


@pytest.mark.parametrize("a,b,c", adc_params)
def test_adc(a, b, c):
    res, carry = a.adc(b, c)
    assert res == a + b + c
    assert carry == (a.zext(1) + b.zext(1) + c)[-1]

def test_adc1():
    a = BV(27734,num_bits=16)
    b = BV(13207,num_bits=16)
    c = BV(0,num_bits=1)
    res, carry = a.adc(b, c)
    assert res == a + b + c
    assert carry == (a.zext(1) + b.zext(1) + c)[-1]
