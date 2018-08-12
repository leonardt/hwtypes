from bit_vector import BitVector

def test_concat():
    a = BitVector(4, 4)
    b = BitVector(1, 4)
    c = BitVector.concat(a, b)
    expected = BitVector([1,0,0,0,0,0,1,0])
    assert expected == c
