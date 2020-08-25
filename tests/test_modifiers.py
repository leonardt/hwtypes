import pytest

from hwtypes import Bit, BitVector, AbstractBit
import hwtypes.modifiers as modifiers
from hwtypes.modifiers import make_modifier, is_modified, is_modifier, unwrap_modifier, wrap_modifier
from hwtypes.modifiers import get_modifier, get_unmodified
from hwtypes.modifiers import strip_modifiers, push_modifiers
from hwtypes.adt import Tuple, Product, Sum, Enum, TaggedUnion

modifiers._DEBUG = True

def test_basic():
    Global = make_modifier("Global")
    GlobalBit = Global(Bit)

    assert GlobalBit is Global(Bit)

    assert issubclass(GlobalBit, Bit)
    assert issubclass(GlobalBit, AbstractBit)
    assert issubclass(GlobalBit, Global)
    assert issubclass(GlobalBit, Global(AbstractBit))

    global_bit = GlobalBit(0)

    assert isinstance(global_bit, GlobalBit)
    assert isinstance(global_bit, Bit)
    assert isinstance(global_bit, AbstractBit)
    assert isinstance(global_bit, Global)
    assert isinstance(global_bit, Global(AbstractBit))

    assert is_modifier(Global)
    assert is_modified(GlobalBit)
    assert not is_modifier(Bit)
    assert not is_modified(Bit)
    assert not is_modified(Global)

    assert get_modifier(GlobalBit) is Global
    assert get_unmodified(GlobalBit) is Bit

    with pytest.raises(TypeError):
        get_modifier(Bit)

    with pytest.raises(TypeError):
        get_unmodified(Bit)


def test_modify_adt():
    Mod = make_modifier("Mod")

    T = Tuple[int, str]
    MT = Mod(T)
    assert issubclass(MT, T)
    assert MT(0, 'y')[0] == 0
    assert MT(0, 'y')[1] == 'y'

    class P(Product):
        x = int
        y = str

    MP = Mod(P)
    assert issubclass(MP, T)
    assert issubclass(MP, P)
    assert issubclass(MP, MT)
    assert MP(x=0, y='y').y == 'y'
    assert MP(y='y', x=0).x == 0

    S = Sum[int, str]
    MS = Mod(S)
    assert issubclass(MS, S)
    assert MS(0)[int].value == 0
    assert MS('x')[str].value == 'x'


def test_cache():
    G1 = make_modifier("Global", cache=True)
    G2 = make_modifier("Global", cache=True)
    G3 = make_modifier("Global")

    assert G1 is G2
    assert G1 is not G3

def test_nested():
    A = make_modifier("A")
    B = make_modifier("B")
    C = make_modifier("C")
    ABCBit = C(B(A(Bit)))
    base, mods = unwrap_modifier(ABCBit)
    assert base is Bit
    assert mods == [A, B, C]
    assert wrap_modifier(Bit, mods) == ABCBit
    with pytest.raises(TypeError):
        wrap_modifier(Bit, [A, B, C, A])

def test_strip():
    M0 = make_modifier("M0")
    M1 = make_modifier("M1")
    M2 = make_modifier("M2")
    BV = BitVector

    class E(Enum):
        a=1
        b=2
    class A(Product, cache=True):
        b = M0(Sum[Bit, M1(BV[6]), M2(E)])
        c = M1(E)
        d = M2(Tuple[M0(BV[3]), M1(M0(Bit))])

    A_stripped = strip_modifiers(A)
    assert A_stripped.b is Sum[Bit, BV[6], E]
    assert A_stripped.c is E
    assert A_stripped.d is Tuple[BV[3], Bit]

def test_ta_strip():
    class Ta(TaggedUnion, cache=True):
        a = int
        b = int
        c = str
    class B(Ta): pass
    class C(B): pass
    M0 = make_modifier("M0")

    C_stripped = strip_modifiers(M0(C))
    assert C == C_stripped

def test_push():
    M0 = make_modifier("M0")
    M1 = make_modifier("M1")
    M2 = make_modifier("M2")
    BV = BitVector

    class E(Enum):
        a=1
        b=2
    class A(Product, cache=True):
        b = M0(Sum[Bit, M1(BV[6]), M2(E)])
        c = M1(E)
        d = M2(Tuple[M0(BV[3]), M1(M0(Bit))])

    A_pushed = push_modifiers(A)
    A_pushed.b is Sum[M0(Bit), M0(M1(BV[6])), M0(M2(E))]
    A_pushed.c is M1(E)
    A_pushed.d is Tuple[M2(M0(BV[3])), M2(M1(M0(Bit)))]
