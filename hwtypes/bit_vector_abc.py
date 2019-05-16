from abc import ABCMeta, abstractmethod
from collections import namedtuple
import typing as tp
import functools as ft
import weakref
import warnings


TypeFamily = namedtuple('TypeFamily', ['Bit', 'BitVector', 'Unsigned', 'Signed'])

#I want to be able differentiate an old style call
#BitVector(val, None) from BitVector(val)
_MISSING = object()
class AbstractBitVectorMeta(ABCMeta):
    # BitVectorType, size :  BitVectorType[size]
    _class_cache = weakref.WeakValueDictionary()

    # BitVectorType : UnsizedBitVectorType, size
    _class_info  = weakref.WeakKeyDictionary()

    def __call__(cls, value=_MISSING, size=_MISSING, *args, **kwargs):
        if cls.is_sized and size is not _MISSING:
            raise TypeError('Cannot use old style construction on sized types')
        elif cls.is_sized:
            if value is _MISSING:
                return super().__call__(*args, **kwargs)
            else:
                return super().__call__(value, *args, **kwargs)
        elif size is _MISSING or size is None:
            if size is None:
                warnings.warn('DEPRECATION WARNING: Use of BitVectorT(value, size) is deprecated')

            if value is _MISSING:
                raise TypeError('Cannot construct {} without a value'.format(cls, value))
            elif isinstance(value, AbstractBitVector):
                size = value.size
            elif isinstance(value, AbstractBit):
                size = 1
            elif isinstance(value, tp.Sequence):
                size = max(len(value), 1)
            elif isinstance(value, int):
                size = max(value.bit_length(), 1)
            elif hasattr(value, '__int__'):
                size = max(int(value).bit_length(), 1)
            else:
                raise TypeError('Cannot construct {} from {}'.format(cls, value))
        else:
            warnings.warn('DEPRECATION WARNING: Use of BitVectorT(value, size) is deprecated')

        return type(cls).__call__(cls[size], value)


    def __new__(mcs, name, bases, namespace, **kwargs):
        size = None
        for base in bases:
            if getattr(base, 'is_sized', False):
                if size is None:
                    size = base.size
                elif size != base.size:
                    raise TypeError("Can't inherit from multiple different sizes")

        t = super().__new__(mcs, name, bases, namespace, **kwargs)
        if size is None:
            mcs._class_info[t] = t, size
        else:
            mcs._class_info[t] = None, size

        return t


    def __getitem__(cls, idx : int) -> 'AbstractBitVectorMeta':
        mcs = type(cls)
        try:
            return mcs._class_cache[cls, idx]
        except KeyError:
            pass

        if not isinstance(idx, int):
            raise TypeError('Size of BitVectors must be of type int not {}'.format(type(idx)))
        if idx < 0:
            raise ValueError('Size of BitVectors must be positive')

        if cls.is_sized:
            raise TypeError('{} is already sized'.format(cls))

        bases = [cls]
        bases.extend(b[idx] for b in cls.__bases__ if isinstance(b, mcs))
        bases = tuple(bases)
        class_name = '{}[{}]'.format(cls.__name__, idx)
        t = mcs(class_name, bases, {})
        t.__module__ = cls.__module__
        mcs._class_cache[cls, idx] = t
        mcs._class_info[t] = cls, idx
        return t

    @property
    def unsized_t(cls) -> 'AbstractBitVectorMeta':
        t = type(cls)._class_info[cls][0]
        if t is not None:
            return t
        else:
            raise AttributeError('type {} has no unsized_t'.format(cls))

    @property
    def size(cls) -> int:
        return type(cls)._class_info[cls][1]

    @property
    def is_sized(cls) -> bool:
        return type(cls)._class_info[cls][1] is not None

class AbstractBit(metaclass=ABCMeta):
    @staticmethod
    def get_family() -> TypeFamily:
        return _Family_

    @abstractmethod
    def __eq__(self, other) -> 'AbstractBit':
        pass

    def __ne__(self, other) -> 'AbstractBit':
        return ~(self == other)

    @abstractmethod
    def __invert__(self) -> 'AbstractBit':
        pass

    @abstractmethod
    def __and__(self, other : 'AbstractBit') -> 'AbstractBit':
        pass

    @abstractmethod
    def __or__(self, other : 'AbstractBit') -> 'AbstractBit':
        pass

    @abstractmethod
    def __xor__(self, other : 'AbstractBit') -> 'AbstractBit':
        pass

    @abstractmethod
    def ite(self, t_branch, f_branch):
        pass

class AbstractBitVector(metaclass=AbstractBitVectorMeta):
    @staticmethod
    def get_family() -> TypeFamily:
        return _Family_

    @property
    def size(self) -> int:
        return  type(self).size

    @classmethod
    @abstractmethod
    def make_constant(self, value, num_bits:tp.Optional[int]=None) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def __getitem__(self, index) -> AbstractBit:
        pass

    @abstractmethod
    def __setitem__(self, index : int, value : AbstractBit):
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    #could still be staticmethod but I think thats annoying
    @classmethod
    @abstractmethod
    def concat(cls, x, y) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def bvnot(self) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def bvand(self, other) -> 'AbstractBitVector':
        pass

    def bvnand(self, other) -> 'AbstractBitVector':
        return self.bvand(other).bvnot()

    @abstractmethod
    def bvor(self, other) -> 'AbstractBitVector':
        pass

    def bvnor(self, other) -> 'AbstractBitVector':
        return self.bvor(other).bvnot()

    @abstractmethod
    def bvxor(self, other) -> 'AbstractBitVector':
        pass

    def bvxnor(self, other) -> 'AbstractBitVector':
        return self.bvxor(other).bvnot()

    @abstractmethod
    def bvshl(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def bvlshr(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def bvashr(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def bvrol(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def bvror(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def bvcomp(self, other) -> 'AbstractBitVector[1]':
        pass

    @abstractmethod
    def bveq(self, other) -> AbstractBit:
        pass

    def bvne(self, other) -> AbstractBit:
        return ~self.bveq(other)

    @abstractmethod
    def bvult(self, other) -> AbstractBit:
        pass

    def bvule(self, other) -> AbstractBit:
        return self.bvult(other) | self.bveq(other)

    def bvugt(self, other) -> AbstractBit:
        return ~self.bvule(other)

    def bvuge(self, other) -> AbstractBit:
        return ~self.bvult(other)

    @abstractmethod
    def bvslt(self, other) -> AbstractBit:
        pass

    def bvsle(self, other) -> AbstractBit:
        return self.bvslt(other) | self.bveq(other)

    def bvsgt(self, other) -> AbstractBit:
        return ~self.bvsle(other)

    def bvsge(self, other) -> AbstractBit:
        return ~self.bvslt(other)

    @abstractmethod
    def bvneg(self) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def adc(self, other, carry) -> tp.Tuple['AbstractBitVector', AbstractBit]:
        pass

    @abstractmethod
    def ite(i,t,e) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def bvadd(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def bvsub(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def bvmul(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def bvudiv(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def bvurem(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def bvsdiv(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def bvsrem(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def repeat(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def sext(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def ext(self, other) -> 'AbstractBitVector':
        pass

    @abstractmethod
    def zext(self, other) -> 'AbstractBitVector':
        pass


_Family_ = TypeFamily(AbstractBit, AbstractBitVector, None, None)
