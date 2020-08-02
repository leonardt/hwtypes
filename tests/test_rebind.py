import pytest

from hwtypes.adt import Product, Sum, Enum, Tuple, TaggedUnion
from hwtypes.adt_util import rebind_bitvector, rebind_keep_modifiers, rebind_type
from hwtypes.bit_vector import AbstractBitVector, BitVector, AbstractBit, Bit
from hwtypes.smt_bit_vector import SMTBit, SMTBitVector
from hwtypes.util import _issubclass
from hwtypes.modifiers import make_modifier

class A: pass
class B: pass
class C(A): pass
class D(B): pass

class E(Enum):
    A = 0
    B = 1
    C = 2
    E = 3

T0 = Tuple[A, B, C, E]

class P0(Product, cache=True):
    A = A
    B = B
    C = C
    E = E

S0 = Sum[A, B, C, E]

class P1(Product, cache=True):
    P0 = P0
    S0 = S0
    T0 = T0
    D  = D

S1 = Sum[P0, S0, T0, D]



@pytest.mark.parametrize("type_0", [A, B, C, D, E])
@pytest.mark.parametrize("type_1", [A, B, C, D, E])
@pytest.mark.parametrize("rebind_sub_types", [False, True])
def test_rebind_enum(type_0, type_1, rebind_sub_types):
    assert E is E.rebind(type_0, type_1, rebind_sub_types)


@pytest.mark.parametrize("T", [T0, S0])
@pytest.mark.parametrize("type_0", [A, B, C, D, E])
@pytest.mark.parametrize("type_1", [A, B, C, D, E])
@pytest.mark.parametrize("rebind_sub_types", [False, True])
def test_rebind_sum_tuple(T, type_0, type_1, rebind_sub_types):
    fields = T.fields
    T_ = T.rebind(type_0, type_1, rebind_sub_types)

    if rebind_sub_types:
        map_fn = lambda s : type_1 if _issubclass(s, type_0) else s
    else:
        map_fn = lambda s : type_1 if s == type_0 else s

    new_fields = map(map_fn, fields)

    assert T_ is T.unbound_t[new_fields]


@pytest.mark.parametrize("type_0", [A, B, C, D, E])
@pytest.mark.parametrize("type_1", [A, B, C, D, E])
@pytest.mark.parametrize("rebind_sub_types", [False, True])
def test_rebind_product(type_0, type_1, rebind_sub_types):
    field_dict = P0.field_dict
    P_ = P0.rebind(type_0, type_1, rebind_sub_types)

    if rebind_sub_types:
        map_fn = lambda s : type_1 if _issubclass(s, type_0) else s
    else:
        map_fn = lambda s : type_1 if s == type_0 else s

    new_fields = {}
    for k,v in field_dict.items():
        new_fields[k] = map_fn(v)

    assert P_ is Product.from_fields('P0', new_fields)


@pytest.mark.parametrize("rebind_sub_types", [False, True])
def test_rebind_recursive(rebind_sub_types):
    S_ = S1.rebind(B, A, rebind_sub_types)
    if rebind_sub_types:
        gold = Sum[
            P0.rebind(B, A, rebind_sub_types),
            S0.rebind(B, A, rebind_sub_types),
            T0.rebind(B, A, rebind_sub_types),
            A
        ]
    else:
        gold = Sum[
            P0.rebind(B, A, rebind_sub_types),
            S0.rebind(B, A, rebind_sub_types),
            T0.rebind(B, A, rebind_sub_types),
            D
        ]

    assert S_ is gold

    P_ = P1.rebind(B, A, rebind_sub_types)
    if rebind_sub_types:
        gold = Product.from_fields('P1', {
            'P0' : P0.rebind(B, A, rebind_sub_types),
            'S0' : S0.rebind(B, A, rebind_sub_types),
            'T0' : T0.rebind(B, A, rebind_sub_types),
            'D'  : A
        })
    else:
        gold = Product.from_fields('P1', {
            'P0' : P0.rebind(B, A, rebind_sub_types),
            'S0' : S0.rebind(B, A, rebind_sub_types),
            'T0' : T0.rebind(B, A, rebind_sub_types),
            'D'  : D
        })


    assert P_ is gold


class P(Product):
    X = AbstractBitVector[16]
    S = Sum[AbstractBitVector[4], AbstractBitVector[8]]
    T = Tuple[AbstractBitVector[32]]
    class F(Product):
        Y = AbstractBitVector


def test_rebind_bv():
    P_bound = rebind_bitvector(P, AbstractBitVector, BitVector)
    assert P_bound.X == BitVector[16]
    assert P_bound.S == Sum[BitVector[4], BitVector[8]]
    assert P_bound.T[0] == BitVector[32]
    assert P_bound.F.Y == BitVector

    P_unbound = rebind_bitvector(P_bound, BitVector, AbstractBitVector)
    assert P_unbound.X == AbstractBitVector[16]
    assert P_unbound.S == Sum[AbstractBitVector[4], AbstractBitVector[8]]
    assert P_unbound.T[0] == AbstractBitVector[32]


def test_rebind_bv_Tu():
    class T(TaggedUnion):
        a=AbstractBit
        b=AbstractBitVector[5]

    T_bv_rebound = rebind_bitvector(T, AbstractBitVector, BitVector)
    assert T_bv_rebound.b == BitVector[5]
    T_bit_rebound = T_bv_rebound.rebind(AbstractBit, Bit, True)
    assert T_bit_rebound.b == BitVector[5]
    assert T_bit_rebound.a == Bit

def test_issue_74():
    class A(Product):
        a = Bit

    A_smt = A.rebind(AbstractBit, SMTBit, True)
    assert A_smt.a is SMTBit

def test_rebind_mod():
    M = make_modifier("M")
    class A(Product):
        a=M(Bit)
        b=M(BitVector[4])

    A_smt = rebind_bitvector(A,AbstractBitVector, SMTBitVector, True)
    A_smt = rebind_keep_modifiers(A_smt, AbstractBit, SMTBit)
    assert A_smt.b == M(SMTBitVector[4])
    assert A_smt.a == M(SMTBit)

#Tests an issue with rebind_bitvector and Sum
#The issue:
#   If we had Sum[A,B] and A was contained within B
#   (like a field of a Tuple or Product), rebind would fail non-deterministically.
def test_sum_issue():
    for _ in range(1000):
        BV = BitVector
        SBV = SMTBitVector
        T = Tuple[BV[8],BV[1]]
        T_smt = rebind_bitvector(T,AbstractBitVector,SMTBitVector, True)
        S = Sum[T,BV[8]]
        S_smt = rebind_bitvector(S,AbstractBitVector,SMTBitVector, True)
        assert T_smt in S_smt.fields

def test_rebind_type():
    class E(Enum):
        a=1
        b=2
    def gen_type(family):
        Bit = family.Bit
        BV = family.BitVector
        class A(Product, cache=True):
            a=Sum[Bit,BV[8],E]
            b=BV[16]
            c=Tuple[E,Bit,BV[7]]
        return A
    A_bv = gen_type(Bit.get_family())
    A_smt = gen_type(SMTBit.get_family())
    Ar_smt = rebind_type(A_bv, SMTBit.get_family())
    Ar_bv = rebind_type(A_smt, Bit.get_family())
    assert A_bv == Ar_bv
    assert A_smt == Ar_smt
