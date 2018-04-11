from bit_vector import BitVector

def test_simple():
    a = BitVector(4, 4)
    assert int(a) == 4

def test_negative():
    a = BitVector(-4, 4, signed=True)
    assert a._value != 4, "Stored as unsigned two's complement value"
    assert int(a) == -4, "int returns the native signed int representation"
