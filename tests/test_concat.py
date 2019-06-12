from hwtypes import BitVector
import random

NTESTS = 10
MAX_BITS = 128

def test_concat_const():
    a = BitVector[4](4)
    b = BitVector[4](1)
    c = a.concat(b)
    print(a.binary_string())
    print(c.binary_string())
    expected = BitVector[8]([0,0,1,0,1,0,0,0])
    assert expected == c

def test_concat_random():
    for _ in range(NTESTS):
        n1 = random.randint(1, MAX_BITS)
        n2 = random.randint(1, MAX_BITS)
        a = BitVector.random(n1)
        b = BitVector.random(n2)
        c = a.concat(b)
        assert c.size == a.size + b.size
        assert c == BitVector[n1 + n2](a.bits() + b.bits())
        assert c.binary_string() == b.binary_string() + a.binary_string()
