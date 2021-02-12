from hwtypes import Bit, BitVector, UIntVector, SIntVector


def test_hash():
    x = {
        Bit(0): 0,
        BitVector[3](0): 1,
        UIntVector[3](): 2,
        SIntVector[3](0): 3,
    }
    assert x[Bit(0)] == 0
    assert x[BitVector[3](0)] == 1
    assert x[UIntVector[3](0)] == 2
    assert x[SIntVector[3](0)] == 3
