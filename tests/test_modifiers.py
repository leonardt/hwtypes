import pytest

from hwtypes import Bit, AbstractBit
import hwtypes.modifiers as modifiers
from hwtypes.modifiers import make_modifier, is_modified, is_modifier
from hwtypes.modifiers import get_modifier, get_unmodified
from hwtypes.adt import Tuple, Product, Sum

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

    class P(Product):
        x = int
        y = str

    MP = Mod(P)
    assert issubclass(MP, T)
    assert issubclass(MP, P)
    assert issubclass(MP, MT)

    S = Sum[int, str]
    MS = Mod(S)
    assert issubclass(MS, S)
    assert MS(0).value == 0


def test_cache():
    G1 = make_modifier("Global", cache=True)
    G2 = make_modifier("Global", cache=True)
    G3 = make_modifier("Global")

    assert G1 is G2
    assert G1 is not G3
