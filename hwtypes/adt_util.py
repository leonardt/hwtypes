from abc import ABCMeta, abstractmethod
from .adt_meta import BoundMeta
from .bit_vector_abc import AbstractBitVectorMeta, AbstractBitVector, AbstractBit

from .util import _issubclass
from hwtypes.modifiers import unwrap_modifier, wrap_modifier, is_modified
from .adt import Product, Sum, Tuple, Enum, TaggedUnion
from inspect import isclass



class _ADTVisitor(metaclass=ABCMeta):
    def visit(self, adt_t):
        # The order here is important because Product < Tuple
        # and TaggedUnion < Sum
        if self.check_t(adt_t, Enum):
            self.visit_Enum(adt_t)
        elif self.check_t(adt_t, Product):
            self.visit_Product(adt_t)
        elif self.check_t(adt_t, Tuple):
            self.visit_Tuple(adt_t)
        elif self.check_t(adt_t, TaggedUnion):
            self.visit_TaggedUnion(adt_t)
        elif self.check_t(adt_t, Sum):
            self.visit_Sum(adt_t)
        else:
            self.visit_leaf(adt_t)

    @abstractmethod
    def check_t(self, adt_t): pass

    @abstractmethod
    def generic_visit(self, adt_t): pass

    def visit_Leaf(self, adt_t):  pass

    def visit_Enum(self, adt_t): pass

    def visit_Product(self, adt_t):
        self.generic_visit(adt_t)

    def visit_Tuple(self, adt_t):
        self.generic_visit(adt_t)

    def visit_TaggedUnion(self, adt_t):
        self.generic_visit(adt_t)

    def visit_Sum(self, adt_t):
        self.generic_visit(adt_t)


class ADTVisitor(_ADTVisitor):
    '''
    Visitor for ADTs
    '''
    check_t = staticmethod(_issubclass)

    def generic_visit(self, adt_t):
        for T in adt_t.field_dict.values():
            self.visit(T)


class ADTInstVisitor(_ADTVisitor):
    '''
    Visitor for ADT instances
    '''
    check_t = staticmethod(isinstance)


    def generic_visit(self, adt):
        for k, v in adt.value_dict.items():
            if v is not None:
                self.visit(v)

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

#rebind_type will rebind a type to a different family
#Types that will be rebinded:
#   Product,Tuple,Sum, BitVector, Bit
#   Modified types
#If the passed in type cannot be rebinded, it will just be returned unmodified
def rebind_type(T, family):
    def _rebind_bv(T):
        return rebind_bitvector(T, AbstractBitVector, family.BitVector).rebind(AbstractBit, family.Bit, True)
    if not isclass(T):
        return T
    elif is_modified(T):
        return get_modifier(T)(rebind_type(get_unmodified(T), family, dont_rebind, do_rebind, is_magma))
    elif issubclass(T, AbstractBitVector):
        return rebind_bitvector(T, AbstractBitVector, family.BitVector)
    elif issubclass(T, AbstractBit):
        return family.Bit
    elif issubclass(T, (Product, Tuple, Sum)):
        return _rebind_bv(T)
    else:
        return T
