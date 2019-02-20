from abc import ABCMeta, abstractmethod
import typing as tp
import weakref

class AbstractBitVectorMeta(ABCMeta):
    _class_cache = weakref.WeakValueDictionary()
    _class_info  = weakref.WeakKeyDictionary()

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
            AbstractBitVectorMeta._class_info[t] = t, size
        else:
            AbstractBitVectorMeta._class_info[t] = None, size

        return t



    def __getitem__(cls, idx : int) -> tp.Type['AbstractBitVector']:
        try:
            return AbstractBitVector._class_cache[cls, idx]
        except KeyError:
            pass

        if not isinstance(idx, int):
            raise TypeError()
        if idx < 0:
            raise ValueError('Size of BitVectors must be positive')

        if cls.is_sized:
            raise TypeError('Cannot generate sized from sized')

        bases = [cls]
        bases.extend(b[idx] for b in cls.__bases__ if isinstance(b, AbstractBitVectorMeta))
        bases = tuple(bases)
        class_name = '{}[{}]'.format(cls.__name__, idx)
        t = type(cls)(class_name, bases, {})
        t.__module__ = cls.__module__
        AbstractBitVectorMeta._class_cache[cls, idx] = t
        AbstractBitVectorMeta._class_info[t] = cls, idx
        return t

    @property
    def unsized_t(cls):
        return AbstractBitVectorMeta._class_info[cls][0]

    @property
    def size(cls):
        return AbstractBitVectorMeta._class_info[cls][1]

    @property
    def is_sized(cls):
        return AbstractBitVectorMeta._class_info[cls][1] is not None


class AbstractBitVector(metaclass=AbstractBitVectorMeta):
    def __new__(cls, value):
        if cls.is_sized:
            return super().__new__(cls)

        size = int(value).bit_length()
        return cls[size].__new__(cls[size], value)

    @abstractmethod
    def __init__(self):
        pass

    @property
    def size(self):
        return  type(self).size

    @abstractmethod
    def make_constant(self, value, num_bits:tp.Optional[int]=None):
        pass

    @abstractmethod
    def __getitem__(self, index):
        pass

    @abstractmethod
    def __len__(self):
        pass

    #could still be staticmethod but I think thats annoying
    @classmethod
    @abstractmethod
    def concat(cls, x, y):
        pass

    @abstractmethod
    def bvnot(self):
        pass

    @abstractmethod
    def bvand(self, other):
        pass

    def bvnand(self, other):
        return self.bvand(other).bvnot()

    @abstractmethod
    def bvor(self, other):
        pass

    def bvnor(self, other):
        return self.bvor(other).bvnot()

    @abstractmethod
    def bvxor(self, other):
        pass

    def bvxnor(self, other):
        return self.bvxor(other).bvnot()

    @abstractmethod
    def bvshl(self, other):
        pass

    @abstractmethod
    def bvlshr(self, other):
        pass

    @abstractmethod
    def bvashr(self, other):
        pass

    @abstractmethod
    def bvrol(self, other):
        pass

    @abstractmethod
    def bvror(self, other):
        pass

    @abstractmethod
    def bvcomp(self, other):
        pass

    def bveq(self, other):
        return self.bvcomp(other)

    def bvne(self, other):
        return self.bvcomp(other).bvnot()

    @abstractmethod
    def bvult(self, other):
        pass

    def bvule(self, other):
        return self.bvult(other).bvor(self.bvcomp(other))

    def bvugt(self, other):
        return self.bvule(other).bvnot()

    def bvuge(self, other):
        return self.bvult(other).bvnot()

    @abstractmethod
    def bvslt(self, other):
        pass

    def bvsle(self, other):
        return self.bvslt(other).bvor(self.bvcomp(other))

    def bvsgt(self, other):
        return self.bvsle(other).bvnot()

    def bvsge(self, other):
        return self.bvslt(other).bvnot()

    @abstractmethod
    def bvneg(self):
        pass

    @abstractmethod
    def adc(self, other, carry):
        pass

    @abstractmethod
    def ite(i,t,e):
        pass

    @abstractmethod
    def bvadd(self, other):
        pass

    def bvsub(self, other):
        return self.bvadd(other.bvneg())

    @abstractmethod
    def bvmul(self, other):
        pass

    @abstractmethod
    def bvudiv(self, other):
        pass

    @abstractmethod
    def bvurem(self, other):
        pass

    @abstractmethod
    def bvsdiv(self, other):
        pass

    @abstractmethod
    def bvsrem(self, other):
        pass

    @abstractmethod
    def repeat(self, other):
        pass

    @abstractmethod
    def sext(self, other):
        pass

    @abstractmethod
    def ext(self, other):
        pass

    @abstractmethod
    def zext(self, other):
        pass
