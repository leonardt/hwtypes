from hwtypes.bit_vector_util import BitVectorProtocol, BitVectorProtocolMeta
from hwtypes import BitVector, Bit

Word = BitVector[32]


class CounterMeta(type):
    def _bitvector_t_(cls):
        return Word


class Counter(metaclass=CounterMeta):
    def __init__(self):
        self._cnt : Word = Word(0)

    @classmethod
    def _from_bitvector_(cls, bv: Word) -> 'cls':
        obj = cls()
        obj._cnt = bv
        return obj

    def _to_bitvector_(self) -> Word:
        return self._cnt

    def inc(self):
        self._cnt += 1

    @property
    def val(self):
        return self._cnt


def test_implicit_inheritance():
    assert isinstance(Counter(), BitVectorProtocol)
    assert issubclass(Counter, BitVectorProtocolMeta)


def test_protocol_ite():
    cnt1 = Counter()
    cnt2 = Counter()

    cnt1.inc()

    assert cnt1.val == 1
    assert cnt2.val == 0

    cnt3 = Bit(0).ite(cnt1, cnt2)

    assert cnt3.val == cnt2.val

    cnt4 = Bit(1).ite(cnt1, cnt2)

    assert cnt4.val == cnt1.val
