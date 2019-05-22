from hwtypes.modifiers import make_modifier
from hwtypes import Bit, AbstractBit


def test_basic():
    Global = make_modifier("Global")
    GlobalBit = Global(Bit)

    assert issubclass(GlobalBit, Bit)
    assert issubclass(GlobalBit, AbstractBit)
    assert issubclass(GlobalBit, Global)

    global_bit = GlobalBit(0)

    assert isinstance(global_bit, GlobalBit)
    assert isinstance(global_bit, Bit)
    assert isinstance(global_bit, AbstractBit)
    assert isinstance(global_bit, Global)

def test_cache():
    G1 = make_modifier("Global", cache=True)
    G2 = make_modifier("Global", cache=True)
    G3 = make_modifier("Global")

    assert G1 is G2
    assert G1 is not G3

