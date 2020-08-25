import pytest

from hwtypes.util import TypedProperty

def test_typedproperty():
    class A:
        _x  : int
        def __init__(self, x):
            self.x = x

        @TypedProperty(int)
        def x(self):
            return self._x

        @x.setter
        def x(self, val):
            self._x = val

        @TypedProperty(str)
        def foo(self):
            return 'foo'

        @property
        def bar(self):
            return 'bar'

    assert A.x is int
    assert A.foo is str

    a = A(0)

    assert a.x == 0
    a.x = 1
    assert a.x == 1
    assert a.foo == 'foo'

    with pytest.raises(TypeError):
        a.x = 'a'

    with pytest.raises(AttributeError):
        class B(A):
            @A.foo.setter
            def foo(self, value):
                pass

    class C(A):
        @A.bar.setter
        def bar(self, value):
            pass
