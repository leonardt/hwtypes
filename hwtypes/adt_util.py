from .adt_meta import BoundMeta
from .bit_vector_abc import AbstractBitVectorMeta, AbstractBitVector

from .util import _issubclass

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
