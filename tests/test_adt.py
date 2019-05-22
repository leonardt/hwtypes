import pytest
from hwtypes.adt import Product, Sum, Enum, Tuple
from hwtypes.modifiers import new

class En(Enum):
    a = 0
    b = 1

class Pr(Product):
    x = En
    y = En

Su = Sum[En, Pr]

Tu = Tuple[En, En]

def test_enum():
    assert set(En.enumerate()) == {
            En.a,
            En.b,
    }

    assert En.a.value == 0
    assert En.a is En.a

    assert issubclass(En, Enum)
    assert isinstance(En.a, Enum)
    assert isinstance(En.a, En)

def test_tuple():
    assert set(Tu.enumerate()) == {
            Tu(En.a, En.a),
            Tu(En.a, En.b),
            Tu(En.b, En.a),
            Tu(En.b, En.b),
    }

    assert Tu(En.a, En.a).value == (En.a, En.a)

    assert issubclass(Tu, Tuple)
    assert isinstance(Tu(En.a, En.a), Tuple)
    assert isinstance(Tu(En.a, En.a), Tu)

    t = Tu(En.a, En.b)
    assert (t[0],t[1]) == (En.a,En.b)
    t[0] = En.b
    assert (t[0],t[1]) == (En.b,En.b)

    with pytest.raises(TypeError):
        Tu(En.a, 1)

    with pytest.raises(TypeError):
        t[1] = 1

def test_product():
    assert set(Pr.enumerate()) == {
            Pr(En.a, En.a),
            Pr(En.a, En.b),
            Pr(En.b, En.a),
            Pr(En.b, En.b),
    }

    assert Pr(En.a, En.a).value == (En.a, En.a)

    assert issubclass(Pr, Product)
    assert isinstance(Pr(En.a, En.a), Product)
    assert isinstance(Pr(En.a, En.a), Pr)

    assert Pr(En.a, En.b) == Tu(En.a, En.b)
    assert issubclass(Pr, Tu)
    assert issubclass(Pr, Tuple)
    assert isinstance(Pr(En.a, En.b), Tu)

    assert Pr[0] == Pr.x == En
    assert Pr[1] == Pr.y == En

    assert Pr.field_dict == {'x' : En, 'y' : En }
    assert Pr(En.b, En.a).value_dict == {'x' : En.b, 'y' : En.a}

    p = Pr(En.a, En.b)
    assert p[0] == p.x == En.a
    assert p[1] == p.y == En.b
    p.x = En.b
    assert p[0] == p.x == En.b
    p[0] = En.a
    assert p[0] == p.x == En.a

    with pytest.raises(TypeError):
        Pr(En.a, 1)

    with pytest.raises(TypeError):
        p[0] = 1

def test_sum():
    assert set(Su.enumerate()) == {
            Su(En.a),
            Su(En.b),
            Su(Pr(En.a, En.a)),
            Su(Pr(En.a, En.b)),
            Su(Pr(En.b, En.a)),
            Su(Pr(En.b, En.b)),
    }

    assert Su(En.a).value == En.a

    assert issubclass(Su, Sum)
    assert isinstance(Su(En.a), Su)
    assert isinstance(Su(En.a), Sum)

    assert Su.field_dict == {'En' : En, 'Pr' : Pr}
    assert Su(En.a).value_dict == {'En' : En.a, 'Pr' : None}

    with pytest.raises(TypeError):
        Su(1)


def test_new():
    t = new(Tuple)
    s = new(Tuple)
    assert issubclass(t, Tuple)
    assert issubclass(t[En], t)
    assert issubclass(t[En], Tuple[En])
    assert t is not Tuple
    assert s is not t

    t = new(Sum, (En, Pr))
    assert t is not Su
    assert Sum[En, Pr] is Su
    assert t.__module__ == 'hwtypes.modifiers'

    t = new(Sum, (En, Pr), module=__name__)
    assert t.__module__ == __name__
