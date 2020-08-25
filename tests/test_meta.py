import pytest
from hwtypes import AbstractBitVector as ABV
from hwtypes import BitVector as BV

def test_subclass():
    class A(ABV): pass
    class B(ABV): pass
    class C(A): pass
    class D(A, B): pass
    class E(ABV[8]): pass

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


    assert issubclass(E, ABV[8])
    assert issubclass(E, ABV)

    with pytest.raises(TypeError):
        ABV[8][2]

    with pytest.raises(TypeError):
        E[2]

    with pytest.raises(TypeError):
        class F(ABV[8], ABV[7]): pass


def test_size():
    class A(ABV): pass

    assert A.size is None
    assert A.unsized_t is A
    bv = A[8]
    assert bv.size == 8
    assert bv.unsized_t is A

    class B(ABV[8]): pass

    assert B.size == 8
    with pytest.raises(AttributeError):
        B.unsized_t

    with pytest.raises(TypeError):
        B[2]

    class C(A, B): pass
    assert C.size == 8
    with pytest.raises(AttributeError):
        C.unsized_t

    with pytest.raises(TypeError):
        C[6]

def test_instance():
    x = BV[8](0)
    assert isinstance(x, ABV)
    assert isinstance(x, ABV[8])
    assert isinstance(x, BV)
    with pytest.raises(TypeError):
        ABV[4](0)

    class A(BV): pass

    y = A[8](0)
    assert isinstance(y, ABV)
    assert isinstance(y, ABV[8])
    assert isinstance(y, BV)
    assert isinstance(y, BV[8])
