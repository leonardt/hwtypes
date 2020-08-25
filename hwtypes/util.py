from collections import OrderedDict
from collections.abc import Mapping, MutableMapping
import typing as tp

class FrozenDict(Mapping):
    __slots__ = '_d', '_hash'

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        self._hash = hash(frozenset(self.items()))

    def __getitem__(self, key):
        return self._d.__getitem__(key)

    def __iter__(self):
        return self._d.__iter__()

    def __len__(self):
        return self._d.__len__()

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._d == other._d
        else:
            return self._d == other

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return self._hash


class OrderedFrozenDict(FrozenDict):
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        self._d = OrderedDict(*args, **kwargs)
        self._hash = hash(tuple(self.items()))


class TypedProperty:
    '''
    Behaves mostly like property except:
        class A:
            @property
            def foo(self): ...

            @foo.setter
            def foo(self, value): ...

        A.Foo -> <property object at 0x...>

        class B:
            @TypedProperty(T)
            def foo(self): ...

            @foo.setter
            def foo(self, value): ...

        B.Foo -> T
        B().foo = T() #works
        B().foo = A() # TypeError expected T not A

        class C(A):
            @A.foo.setter #works

        class D(B):
            @B.foo.setter #error unless T has atrribute setter in which case
                          #T.setter is called for the decorator as B.Foo -> T.
                          #In generalTypedProperty objects must not be modified
                          #outside of the class in which they are declared

    '''
    def __init__(self, T):
        self.T = T
        self.final = False
        self.fget = None
        self.fset = None
        self.fdel = None
        self.__doc__ = None

    def __call__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc
        return self

    def __get__(self, obj, objtype=None):
        if obj is None:
            if self.final:
                return self.T
            else:
                return self

        if self.fget is None:
            raise AttributeError("unreadable attribute")
        return self.fget(obj)

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        elif not isinstance(value, self.T):
            raise TypeError(f'Expected {self.T} not {type(value)}')
        self.fset(obj, value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(obj)

    def __set_name__(self, cls, name):
        self.final = True

    def getter(self, fget):
        return type(self)(self.T)(fget, self.fset, self.fdel, self.__doc__)

    def setter(self, fset):
        return type(self)(self.T)(self.fget, fset, self.fdel, self.__doc__)

    def deleter(self, fdel):
        return type(self)(self.T)(self.fget, self.fset, fdel, self.__doc__)


def _issubclass(sub : tp.Any, parent : type) -> bool:
    try:
        return issubclass(sub, parent)
    except TypeError:
        return False
