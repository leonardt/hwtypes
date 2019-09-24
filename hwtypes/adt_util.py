from .adt_meta import BoundMeta
from .bit_vector_abc import AbstractBitVectorMeta, AbstractBitVector

from .util import _issubclass
from hwtypes.modifiers import unwrap_modifier, wrap_modifier, is_modified

def rebind_bitvector(
        adt,
        bv_type_0: AbstractBitVectorMeta,
        bv_type_1: AbstractBitVectorMeta,
        keep_modifiers=False):
    if keep_modifiers and is_modified(adt):
        unmod, mods = unwrap_modifier(adt)
        return wrap_modifier(rebind_bitvector(unmod,bv_type_0,bv_type_1,True),mods)

    if _issubclass(adt, bv_type_0):
        if adt.is_sized:
            return bv_type_1[adt.size]
        else:
            return bv_type_1
    elif isinstance(adt, BoundMeta):
        _to_new = []
        for field in adt.fields:
            new_field = rebind_bitvector(field, bv_type_0, bv_type_1,keep_modifiers)
            _to_new.append((field,new_field))
        new_adt = adt

        for field,new_field in _to_new:
            new_adt = new_adt.rebind(field, new_field, rebind_recursive=False)
        return new_adt
    else:
        return adt

def rebind_keep_modifiers(adt, A, B):
    if is_modified(adt):
        unmod, mods = unwrap_modifier(adt)
        return wrap_modifier(rebind_keep_modifiers(unmod,A,B),mods)

    if _issubclass(adt,A):
        return B
    elif isinstance(adt, BoundMeta):
        new_adt = adt
        for field in adt.fields:
            new_field = rebind_keep_modifiers(field, A, B)
            new_adt = new_adt.rebind(field, new_field)
        return new_adt
    else:
        return adt
