from hwtypes import BitVector as BV
from hwtypes import SIntVector as SV
import random
import pytest


zext_params = []

for i in range(0, 64):
    n = random.randint(0, (1 << 32 - 1))
    num_bits = random.randint(n.bit_length(), 32)
    ext_amount = 32 - num_bits
    zext_params.append((n, num_bits, ext_amount))


@pytest.mark.parametrize("n,num_bits,ext_amount", zext_params)
def test_zext(n, num_bits, ext_amount):
    a = BV[num_bits](n)
    assert num_bits + ext_amount == a.zext(ext_amount).num_bits
    assert n == a.zext(ext_amount).as_uint()
    assert BV[num_bits + ext_amount](n) == a.zext(ext_amount)


sext_params = []

for i in range(0, 64):
    n = random.randint(-(2 ** 15), (2 ** 15) - 1)
    num_bits = random.randint(n.bit_length() + 1, 17)
    ext_amount = 32 - num_bits
    sext_params.append((n, num_bits, ext_amount))


@pytest.mark.parametrize("n,num_bits,ext_amount", sext_params)
def test_sext(n, num_bits, ext_amount):
    a = SV[num_bits](n)
    assert num_bits + ext_amount == a.sext(ext_amount).num_bits
    assert SV[num_bits + ext_amount](n).bits() == a.sext(ext_amount).bits()
    assert SV[num_bits + ext_amount](n) == a.sext(ext_amount)
