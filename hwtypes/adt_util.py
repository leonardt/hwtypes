from .adt_meta import BoundMeta
from .bit_vector_abc import AbstractBitVectorMeta, AbstractBitVector

from .util import _issubclass

def rebind_bitvector(adt, bv_type: AbstractBitVectorMeta):
    if _issubclass(adt, AbstractBitVector):
        if adt.is_sized:
            return bv_type[adt.size]
        else:
            return bv_type
    elif isinstance(adt, BoundMeta):
        new_adt = adt
        for field in adt.fields:
            new_field = rebind_bitvector(field, bv_type)
            new_adt = new_adt.rebind(field, new_field)
        return new_adt
    else:
        return adt
