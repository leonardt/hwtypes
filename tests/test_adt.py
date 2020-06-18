import pytest
from hwtypes.adt import Product, Sum, Enum, Tuple, TaggedUnion, AnonymousProduct
from hwtypes.adt_meta import RESERVED_ATTRS, ReservedNameError, AttrSyntax, GetitemSyntax
from hwtypes.modifiers import new
from hwtypes.adt_util import rebind_bitvector
from hwtypes import BitVector, AbstractBitVector, Bit, AbstractBit


class En1(Enum):
    a = 0
    b = 1


class En2(Enum):
    c = 0
    d = 1

Tu = Tuple[En1, En2]

Ap = AnonymousProduct[{'x': En1, 'y': En2}]

class Pr(Product):
    x = En1
    y = En2


class Pr2(Product, cache=False):
    x = En1
    y = En2


class Pr3(Product, cache=True):
    y = En2
    x = En1


Su = Sum[En1, Pr]

class Ta(TaggedUnion):
    x = En1
    y = En1
    z = Pr

class Ta2(TaggedUnion, cache=False):
    x = En1
    y = En1
    z = Pr

class Ta3(TaggedUnion, cache=True):
    y = En1
    x = En1
    z = Pr

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
    assert Tu[0] == En1
    assert Tu[1] == En2

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

def test_anonymous_product():
    assert set(Ap.enumerate()) == {
            Ap(En1.a, En2.c),
            Ap(En1.a, En2.d),
            Ap(En1.b, En2.c),
            Ap(En1.b, En2.d),
    }

    assert Ap(En1.a, En2.c)._value_ == (En1.a, En2.c)
    assert issubclass(Ap, AnonymousProduct)
    assert isinstance(Ap(En1.a, En2.c), AnonymousProduct)
    assert isinstance(Ap(En1.a, En2.c), Ap)

    assert Ap(En1.a, En2.c) == Tu(En1.a, En2.c)
    assert issubclass(Ap, Tu)
    assert issubclass(Ap, Tuple)
    assert isinstance(Ap(En1.a, En2.c), Tu)

    assert Ap[0] == Ap.x == En1
    assert Ap[1] == Ap.y == En2

    assert Ap.field_dict == {'x' : En1, 'y' : En2 }

    p = Ap(En1.a, En2.c)
    with pytest.raises(TypeError):
        Ap(En1.a, En1.a)

    assert p[0] == p.x == En1.a
    assert p[1] == p.y == En2.c
    assert p.value_dict == {'x' : En1.a, 'y' : En2.c}

    p.x = En1.b
    assert p[0] == p.x == En1.b
    assert p.value_dict == {'x' : En1.b, 'y' : En2.c}

    p[0] = En1.a
    assert p[0] == p.x == En1.a

    with pytest.raises(TypeError):
        p[0] = En2.c


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

    assert Pr(En1.a, En2.c) == Ap(En1.a, En2.c)
    assert issubclass(Pr, Ap)
    assert issubclass(Pr, AnonymousProduct)
    assert isinstance(Pr(En1.a, En2.c), Ap)

    assert Pr[0] == Pr.x == En1
    assert Pr[1] == Pr.y == En2

    assert Pr.field_dict == {'x' : En1, 'y' : En2 }

    p = Pr(En1.a, En2.c)
    with pytest.raises(TypeError):
        Pr(En1.a, En1.a)

    assert p[0] == p.x == En1.a
    assert p[1] == p.y == En2.c
    assert p.value_dict == {'x' : En1.a, 'y' : En2.c}

    p.x = En1.b
    assert p[0] == p.x == En1.b
    assert p.value_dict == {'x' : En1.b, 'y' : En2.c}

    p[0] = En1.a
    assert p[0] == p.x == En1.a

    with pytest.raises(TypeError):
        p[0] = En2.c


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


def test_product_caching():
    global Pr
    assert Pr is not Pr2
    assert Pr is not Pr3
    assert Pr is Product.from_fields('Pr', {'x' : En1, 'y' : En2 }, cache=True)
    assert Pr.field_dict == Pr2.field_dict
    assert Pr.field_dict != Pr3.field_dict
    Pr_ = Pr

    class Pr(Product):
        y = En2
        x = En1

    # Order matters
    assert Pr_ is not Pr

    class Pr(Product):
        x = En1
        y = En2

    assert Pr_ is Pr




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

    assert Su.field_dict == {En1 : En1, Pr : Pr}

    with pytest.raises(TypeError):
        Su(1)

    s = Su(En1.a)
    assert s[En1].match
    assert not s[Pr].match
    with pytest.raises(TypeError):
        s[En2].match

    assert s[En1].value == En1.a

    with pytest.raises(TypeError):
        s[Pr].value

    assert s.value_dict == {En1 : En1.a, Pr : None}

    s[En1] = En1.b
    assert s[En1].value == En1.b

    s[Pr] = Pr(En1.a, En2.c)
    assert s[Pr].match
    assert not s[En1].match
    assert s[Pr].value == Pr(En1.a, En2.c)

    with pytest.raises(TypeError):
        s[En1].value

    with pytest.raises(TypeError):
        s[En1] = En2.c

    with pytest.raises(TypeError):
        s[Pr] = En1.a

def test_tagged_union():
    assert set(Ta.enumerate()) == {
            Ta(x=En1.a),
            Ta(x=En1.b),
            Ta(y=En1.a),
            Ta(y=En1.b),
            Ta(z=Pr(En1.a, En2.c)),
            Ta(z=Pr(En1.a, En2.d)),
            Ta(z=Pr(En1.b, En2.c)),
            Ta(z=Pr(En1.b, En2.d)),
    }


    assert Ta(x=En1.a)._value_ == En1.a

    assert En1 in Ta
    assert Pr in Ta
    assert En2 not in Ta

    assert issubclass(Ta, TaggedUnion)
    assert isinstance(Ta(x=En1.a), TaggedUnion)
    assert isinstance(Ta(x=En1.a), Ta)

    assert Ta(x=En1.a) == Su(En1.a)
    assert issubclass(Ta, Su)
    assert issubclass(Ta, Sum)
    assert isinstance(Ta(x=En1.a), Su)

    assert Ta.x == Ta.y == Ta[En1] == Su[En1] == En1
    assert Ta.z == Ta[Pr] == Su[Pr] == Pr

    assert Ta.field_dict == {'x': En1, 'y': En1, 'z': Pr}

    t = Ta(x=En1.a)
    with pytest.raises(TypeError):
        Ta(x=En2.c)

    assert t[En1].match and t.x.match and not t.y.match and not t.z.match
    assert t[En1].value == t.x.value == En1.a

    with pytest.raises(TypeError):
        t.y.value

    with pytest.raises(TypeError):
        t.z.value

    assert t.value_dict == {'x': En1.a, 'y': None, 'z': None}

    t.x = En1.b
    assert t[En1].match and t.x.match and not t.y.match and not t.z.match
    assert t[En1].value == t.x.value == En1.b

    t.y = En1.a
    assert t[En1].match and t.y.match and not t.x.match and not t.z.match
    assert t[En1].value == t.y.value == En1.a

    with pytest.raises(TypeError):
        t[En1] = En1.a

    with pytest.raises(TypeError):
        t.z = En1.a

    with pytest.raises(TypeError):
        t.y = En2.c

    assert Ta != Ta2
    assert Ta.field_dict == Ta2.field_dict
    assert Ta is TaggedUnion.from_fields('Ta', {'x': En1, 'y': En1, 'z': Pr}, cache=True)


def test_tagged_union_from_fields():
    T = TaggedUnion.from_fields('T', {'A' : int, 'B' : str})
    assert issubclass(T, TaggedUnion)
    assert issubclass(T, Sum[int, str])
    assert T.A == int
    assert T.B == str
    assert T.__module__ == TaggedUnion.__module__

    assert T is TaggedUnion.from_fields('T', {'A' : int, 'B' : str})

    T2 = TaggedUnion.from_fields('T', {'B' : str, 'A' : int})
    assert T2 is T

    T3 = TaggedUnion.from_fields('T', {'A' : int, 'B' : str}, cache=False)
    assert T3 is not T

    with pytest.raises(TypeError):
        Ta.from_fields('T', {'A' : int, 'B' : str})


def test_tagged_union_caching():
    global Ta
    assert Ta is not Ta2
    assert Ta is not Ta3
    assert Ta is TaggedUnion.from_fields('Ta', Ta3.field_dict, cache=True)
    assert Ta2 is not TaggedUnion.from_fields('Ta2', Ta2.field_dict, cache=True)
    assert Ta2 is not TaggedUnion.from_fields('Ta2', Ta2.field_dict, cache=False)
    assert Ta.field_dict == Ta2.field_dict == Ta3.field_dict

    Ta_ = Ta

    class Ta(TaggedUnion):
        x = En1
        y = En1
        z = Pr

    assert Ta_ is Ta

    class Ta(TaggedUnion):
        y = En1
        x = En1
        z = Pr

    assert Ta_ is Ta


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


@pytest.mark.parametrize("T", [En1, Tu, Su, Pr, Ta])
def test_repr(T):
    s = repr(T)
    assert isinstance(s, str)
    assert s != ''
    for e in T.enumerate():
        s = repr(e)
        assert isinstance(s, str)
        assert s != ''


@pytest.mark.parametrize("T_field",
        [(Enum, '0'), (Product, 'int'), (TaggedUnion, 'int')])
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
    (Ta, TaggedUnion),
    ])
def test_unbound_t(t, base):
    assert t.unbound_t == base
    class sub_t(t): pass
    with pytest.raises(AttributeError):
        sub_t.unbound_t

@pytest.mark.parametrize("val", [
    En1.a, Su(En1.a), Ta(x=En1.a),
    Tu(En1.a, En2.c), Pr(En1.a, En2.c)])
def test_deprecated(val):
    with pytest.warns(DeprecationWarning):
        val.value

def test_adt_syntax():
    # En1, Pr, Su, Tu, Ta
    for T in (En1, Pr, Ta):
        assert isinstance(T, AttrSyntax)
        assert not isinstance(T, GetitemSyntax)

    for T in (Su, Tu):
        assert not isinstance(T, AttrSyntax)
        assert isinstance(T, GetitemSyntax)

    for T in (str, Bit, BitVector[4], AbstractBit, AbstractBitVector[4], int):
        assert not isinstance(T, AttrSyntax)
        assert not isinstance(T, GetitemSyntax)

@pytest.mark.parametrize("adt", [
    Su(En1.a), Ta(x=En1.a),
    Tu(En1.a, En2.c), Pr(En1.a, En2.c), Ap(En1.a, En2.c)])
def test_from_values(adt):
    assert adt == type(adt).from_values(adt.value_dict)
