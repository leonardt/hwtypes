from hwtypes.bit_vector_util import BitVectorProtocol, BitVectorProtocolMeta
from hwtypes import BitVector, Bit
from hwtypes import SMTBitVector, SMTBit


def gen_counter(BitVector):
    Word = BitVector[32]


    class CounterMeta(type):
        def _bitvector_t_(cls):
            return Word


    class Counter(metaclass=CounterMeta):
        def __init__(self, initial_value=0):
            self._cnt : Word = Word(initial_value)

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

    return Counter, CounterMeta, Word


def test_implicit_inheritance():
    assert not issubclass(BitVectorProtocol, BitVectorProtocolMeta)
    Counter, CounterMeta, Word = gen_counter(BitVector)
    counter = Counter()
    assert isinstance(counter, BitVectorProtocol)
    assert isinstance(Counter, BitVectorProtocolMeta)
    assert not isinstance(counter, BitVectorProtocolMeta)

    assert issubclass(Counter, BitVectorProtocol)
    assert issubclass(CounterMeta, BitVectorProtocolMeta)
    assert not issubclass(Counter, BitVectorProtocolMeta)


def test_protocol_ite():
    Counter, CounterMeta, Word = gen_counter(BitVector)
    cnt1 = Counter()
    cnt2 = Counter()

    cnt1.inc()

    assert cnt1.val == 1
    assert cnt2.val == 0

    cnt3 = Bit(0).ite(cnt1, cnt2)

    assert cnt3.val == cnt2.val

    cnt4 = Bit(1).ite(cnt1, cnt2)

    assert cnt4.val == cnt1.val


def test_protocol_ite_smt():
    Counter, CounterMeta, Word = gen_counter(SMTBitVector)

    init = Word(name='init')
    cnt1 = Counter(init)
    cnt2 = Counter(init)

    cnt1.inc()

    # pysmt == is structural equiv
    assert cnt1.val.value == (init.value + 1)
    assert cnt1.val.value != init.value
    assert cnt2.val.value == init.value

    cnt3 = SMTBit(0).ite(cnt1, cnt2)

    assert cnt3.val.value == cnt2.val.value

    cnt4 = SMTBit(1).ite(cnt1, cnt2)

    assert cnt4.val.value == cnt1.val.value

    cond = SMTBit(name='cond')

    cnt5 = cond.ite(cnt1, cnt2)

    assert cnt5.val.value == cond.ite(cnt1.val, cnt2.val).value
