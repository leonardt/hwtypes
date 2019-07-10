import pytest
from hwtypes.adt import Product, Sum, Enum, Tuple
from hwtypes.adt_meta import _RESERVED_NAMES, ReservedNameError
from hwtypes.modifiers import new

class En1(Enum):
    a = 0
    b = 1

class En2(Enum):
    c = 0
    d = 1

class Pr(Product):
    x = En1
    y = En2

Su = Sum[En1, Pr]

Tu = Tuple[En1, En2]

def test_enum():
    assert set(En1.enumerate()) == {
            En1.a,
            En1.b,
    }

    assert En1.a.value == 0
    assert En1.a is En1.a

    assert issubclass(En1, Enum)
    assert isinstance(En1.a, Enum)
    assert isinstance(En1.a, En1)

    with pytest.raises(AttributeError):
        En1.a.b

def test_tuple():
    assert set(Tu.enumerate()) == {
            Tu(En1.a, En2.c),
            Tu(En1.a, En2.d),
            Tu(En1.b, En2.c),
            Tu(En1.b, En2.d),
    }

    assert Tu(En1.a, En2.c).value == (En1.a, En2.c)

    assert issubclass(Tu, Tuple)
    assert isinstance(Tu(En1.a, En2.c), Tuple)
    assert isinstance(Tu(En1.a, En2.c), Tu)

    t = Tu(En1.a, En2.c)
    assert (t[0],t[1]) == (En1.a,En2.c)
    t[0] = En1.b
    assert (t[0],t[1]) == (En1.b,En2.c)

    assert Tu.field_dict == {0 : En1, 1 : En2 }
    assert t.value_dict == {0 : En1.b, 1: En2.c}

    with pytest.raises(TypeError):
        Tu(En1.a, 1)

    with pytest.raises(TypeError):
        t[1] = 1

def test_product():
    assert set(Pr.enumerate()) == {
            Pr(En1.a, En2.c),
            Pr(En1.a, En2.d),
            Pr(En1.b, En2.c),
            Pr(En1.b, En2.d),
    }

    assert Pr(En1.a, En2.c).value == (En1.a, En2.c)

    assert issubclass(Pr, Product)
    assert isinstance(Pr(En1.a, En2.c), Product)
    assert isinstance(Pr(En1.a, En2.c), Pr)

    assert Pr(En1.a, En2.c) == Tu(En1.a, En2.c)
    assert issubclass(Pr, Tu)
    assert issubclass(Pr, Tuple)
    assert isinstance(Pr(En1.a, En2.c), Tu)

    assert Pr[0] == Pr.x == En1
    assert Pr[1] == Pr.y == En2

    p = Pr(En1.a, En2.c)
    assert p[0] == p.x == En1.a
    assert p[1] == p.y == En2.c

    assert Pr.field_dict == {'x' : En1, 'y' : En2 }
    assert Pr(En1.b, En2.c).value_dict == {'x' : En1.b, 'y' : En2.c}

    p = Pr(En1.a, En2.c)
    assert p[0] == p.x == En1.a
    assert p[1] == p.y == En2.c
    p.x = En1.b
    assert p[0] == p.x == En1.b
    p[0] = En1.a
    assert p[0] == p.x == En1.a

    with pytest.raises(TypeError):
        Pr(En1.a, En1.a)

    with pytest.raises(TypeError):
        p[0] = En2.c


def test_sum():
    assert set(Su.enumerate()) == {
            Su(En1.a),
            Su(En1.b),
            Su(Pr(En1.a, En2.c)),
            Su(Pr(En1.a, En2.d)),
            Su(Pr(En1.b, En2.c)),
            Su(Pr(En1.b, En2.d)),
    }

    assert Su(En1.a).value == En1.a

    assert issubclass(Su, Sum)
    assert isinstance(Su(En1.a), Su)
    assert isinstance(Su(En1.a), Sum)

    assert Su.field_dict == {'En1' : En1, 'Pr' : Pr}
    assert Su(En1.a).value_dict == {'En1' : En1.a, 'Pr' : None}

    with pytest.raises(TypeError):
        Su(1)


def test_new():
    t = new(Tuple)
    s = new(Tuple)
    assert issubclass(t, Tuple)
    assert issubclass(t[En1], t)
    assert issubclass(t[En1], Tuple[En1])
    assert t is not Tuple
    assert s is not t

    t = new(Sum, (En1, Pr))
    assert t is not Su
    assert Sum[En1, Pr] is Su
    assert t.__module__ == 'hwtypes.modifiers'

    t = new(Sum, (En1, Pr), module=__name__)
    assert t.__module__ == __name__

@pytest.mark.parametrize("T", [En1, Tu, Su, Pr])
def test_repr(T):
    s = repr(T)
    assert isinstance(s, str)
    assert s != ''
    for e in T.enumerate():
        s = repr(e)
        assert isinstance(s, str)
        assert s != ''


@pytest.mark.parametrize("T_field", [(Enum, '0'), (Product, 'int')])
@pytest.mark.parametrize("field_name", list(_RESERVED_NAMES))
def test_reserved(T_field, field_name):
    T, field = T_field
    l_dict = {'T' : T}
    cls_str = f'''
class _(T):
    {field_name} = {field}
'''
    with pytest.raises(ReservedNameError):
        exec(cls_str, l_dict)


