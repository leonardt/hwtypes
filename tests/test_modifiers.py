from hwtypes.modifiers import make_modifier
from hwtypes import Bit, AbstractBit


def test_basic():
    Global, isglobal = make_modifier("Global")
    GlobalBit = Global(Bit)

    assert issubclass(GlobalBit, Bit)
    assert issubclass(GlobalBit, AbstractBit)

    global_bit = GlobalBit(0)

    assert isinstance(global_bit, GlobalBit)
    assert isinstance(global_bit, Bit)
    assert isinstance(global_bit, AbstractBit)
    assert isglobal(global_bit)

    assert GlobalBit is Global(Bit)
    assert Global is not make_modifier("Global", False)
