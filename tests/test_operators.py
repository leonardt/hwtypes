from bit_vector import BitVector
import pytest
import operator
import random


WIDTH = 32
MASK = (1 << WIDTH) - 1
MUL_MASK = ((1 << (WIDTH * 2)) - 1)


def random_int():
    return random.randint(0, (1 << WIDTH) - 1)


@pytest.mark.parametrize("op, reference", [
                              (operator.and_, lambda x, y: x & y & MASK),
                              (operator.or_, lambda x, y: x | y & MASK),
                              (operator.xor, lambda x, y: x ^ y & MASK),
                              (operator.add, lambda x, y: x + y & MASK),
                              (operator.sub, lambda x, y: x - y & MASK),
                              (operator.floordiv, lambda x, y: x // y & MASK),
                              (operator.mul, lambda x, y: x * y & MUL_MASK),
                              (operator.lshift, lambda x, y: x << y),
                              (operator.rshift, lambda x, y: x >> y),
                              # These don't preserve sign for now since they
                              # are comparisons (result is a boolean)
                              # (operator.eq, lambda x, y: x == y),
                              # (operator.lt, lambda x, y: x < y),
                              # (operator.le, lambda x, y: x <= y),
                              # (operator.gt, lambda x, y: x > y),
                              # (operator.ge, lambda x, y: x >= y),
                          ])
@pytest.mark.parametrize("I0,I1", [
    (random_int(), random_int())
    for _ in range(4)
])
@pytest.mark.parametrize("signed", [True, False])
def test_operator_preserve_signed(op, reference, I0, I1, signed):
    I0 = BitVector(I0, WIDTH, signed)
    if op in [operator.lshift, operator.rshift]:
        # Shift amount can't be signed
        I1 = BitVector(I1, WIDTH, signed=False)
    else:
        I1 = BitVector(I1, WIDTH, signed)
    result = op(I0, I1)
    assert result.signed == signed

