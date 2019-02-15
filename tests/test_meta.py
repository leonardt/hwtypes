from bit_vector import AbstractBitVector as ABV

def test_meta():
    class A(ABV): pass
    class B(ABV): pass
    class C(A): pass
    class D(A, B): pass

    assert issubclass(A, ABV)
    assert issubclass(A[8], ABV)
    assert issubclass(A[8], ABV[8])
    assert not issubclass(A, ABV[8])
    assert not issubclass(A[7], ABV[8])

    assert issubclass(C[8], A)
    assert issubclass(C[8], ABV)
    assert issubclass(C[8], A[8])
    assert issubclass(C[8], ABV[8])

    assert issubclass(D[8], A)
    assert issubclass(D[8], B)
    assert issubclass(D[8], ABV)
    assert issubclass(D[8], A[8])
    assert issubclass(D[8], B[8])
    assert issubclass(D[8], ABV[8])




