from hwtypes import BitVector

def test_concat():
    a = BitVector[4](4)
    b = BitVector[4](1)
    c = BitVector.concat(a, b)
    expected = BitVector[8]([1,0,0,0,0,0,1,0])
    assert expected == c
