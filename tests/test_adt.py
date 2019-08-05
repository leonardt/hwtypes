import pytest
from hwtypes.adt import Product, Sum, Enum, Tuple
from hwtypes.adt_meta import RESERVED_ATTRS, ReservedNameError
from hwtypes.modifiers import new
from hwtypes.adt_util import rebind_bitvector

class En1(Enum):
    a = 0
    b = 1


class En2(Enum):
    c = 0
    d = 1


class Pr(Product, cache=True):
    x = En1
    y = En2


class Pr2(Product):
    x = En1
    y = En2


class Pr3(Product):
    y = En2
    x = En1


Su = Sum[En1, Pr]


Tu = Tuple[En1, En2]


def test_enum():
    assert set(En1.enumerate()) == {
            En1.a,
            En1.b,
    }

    assert En1.a._value_ == 0
    assert En1.a is En1.a

    assert issubclass(En1, Enum)
    assert isinstance(En1.a, Enum)
    assert isinstance(En1.a, En1)
    assert En1.is_bound

    with pytest.raises(AttributeError):
        En1.a.b


def test_tuple():
    assert set(Tu.enumerate()) == {
            Tu(En1.a, En2.c),
            Tu(En1.a, En2.d),
            Tu(En1.b, En2.c),
            Tu(En1.b, En2.d),
    }

    assert Tu(En1.a, En2.c)._value_ == (En1.a, En2.c)

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

    assert Pr(En1.a, En2.c)._value_ == (En1.a, En2.c)

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

    assert Pr != Pr2
    assert Pr is Product.from_fields('Pr', {'x' : En1, 'y' : En2 }, cache=True)
    assert Pr.field_dict == Pr2.field_dict
    assert Pr.field_dict != Pr3.field_dict


def test_product_from_fields():
    P = Product.from_fields('P', {'A' : int, 'B' : str})
    assert issubclass(P, Product)
    assert issubclass(P, Tuple[int, str])
    assert P.A == int
    assert P.B == str
    assert P.__module__ == Product.__module__

    assert P is Product.from_fields('P', {'A' : int, 'B' : str})

    P2 = Product.from_fields('P', {'B' : str, 'A' : int})
    assert P2 is not P

    P3 = Product.from_fields('P', {'A' : int, 'B' : str}, cache=False)
    assert P3 is not P
    assert P3 is not P2

    with pytest.raises(TypeError):
        Pr.from_fields('P', {'A' : int, 'B' : str})


def test_sum():
    assert set(Su.enumerate()) == {
            Su(En1.a),
            Su(En1.b),
            Su(Pr(En1.a, En2.c)),
            Su(Pr(En1.a, En2.d)),
            Su(Pr(En1.b, En2.c)),
            Su(Pr(En1.b, En2.d)),
    }

    assert Su(En1.a)._value_ == En1.a

    assert En1 in Su
    assert Pr in Su
    assert En2 not in Su

    assert issubclass(Su, Sum)
    assert isinstance(Su(En1.a), Su)
    assert isinstance(Su(En1.a), Sum)

    assert Su[En1] == En1
    assert Su[Pr] == Pr
    with pytest.raises(KeyError):
        Su[En2]

    assert Su.field_dict == {'En1' : En1, 'Pr' : Pr}

    with pytest.raises(TypeError):
        Su(1)

    s = Su(En1.a)
    assert En1 in s
    assert Pr not in s
    with pytest.raises(TypeError):
        En2 in s

    assert s[En1] == En1.a

    with pytest.raises(KeyError):
        s[Pr]


    assert s.value_dict == {'En1' : En1.a, 'Pr' : None}

    s[En1] = En1.b
    assert s[En1] == En1.b

    s[Pr] = Pr(En1.a, En2.c)
    assert Pr in s
    assert En1 not in s
    assert s[Pr] == Pr(En1.a, En2.c)

    with pytest.raises(KeyError):
        s[En1]

    with pytest.raises(TypeError):
        s[En1] = En2.c

    with pytest.raises(TypeError):
        s[Pr] = En1.a

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
@pytest.mark.parametrize("field_name", list(RESERVED_ATTRS))
def test_reserved(T_field, field_name):
    T, field = T_field
    l_dict = {'T' : T}
    cls_str = f'''
class _(T):
    {field_name} = {field}
'''
    with pytest.raises(ReservedNameError):
        exec(cls_str, l_dict)

@pytest.mark.parametrize("t, base", [
    (En1, Enum),
    (Pr, Product),
    (Su, Sum),
    (Tu, Tuple),
    ])
def test_unbound_t(t, base):
    assert t.unbound_t == base
    class sub_t(t): pass
    with pytest.raises(AttributeError):
        sub_t.unbound_t

@pytest.mark.parametrize("val", [
    En1.a, Su(En1.a),
    Tu(En1.a, En2.c), Pr(En1.a, En2.c)])
def test_deprecated(val):
    with pytest.warns(DeprecationWarning):
        val.value
