from .adt_meta import BoundMeta
from .bit_vector_abc import AbstractBitVectorMeta, AbstractBitVector

from .util import _issubclass
from hwtypes.modifiers import get_all_modifiers

def rebind_bitvector(
        adt,
        bv_type_0: AbstractBitVectorMeta,
        bv_type_1: AbstractBitVectorMeta):
    if _issubclass(adt, bv_type_0):
        if adt.is_sized:
            return bv_type_1[adt.size]
        else:
            return bv_type_1
    elif isinstance(adt, BoundMeta):
        new_adt = adt
        for field in adt.fields:
            new_field = rebind_bitvector(field, bv_type_0, bv_type_1)
            new_adt = new_adt.rebind(field, new_field)
        return new_adt
    else:
        return adt


def rebind_keep_modifiers(adt, A, B, rebind_sub_types=False):
    if A is B or (rebind_sub_types and _issubclass(adt, B)):
        for mod in get_all_modifiers(A):
            B = mod(B)
        return B
    elif isinstance(adt, BoundMeta):
        new_adt = adt
        for field in adt.fields:
            new_field = rebind_keep_modifiers(field, A, B, rebind_sub_types)
            new_adt = new_adt.rebind(field, new_field)
        return new_adt
    else:
        return adt
