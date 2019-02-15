from abc import ABCMeta, abstractmethod
import typing as tp
import weakref

class AbstractBitVectorMeta(ABCMeta):
    _class_cache = weakref.WeakValueDictionary()
    def __getitem__(cls, idx : int) -> 'AbstractBitVector':
        try:
            return AbstractBitVector._class_cache[cls, idx]
        except KeyError:
            pass

        if not isinstance(idx, int):
            raise TypeError()
        if idx < 0:
            raise ValueError('Size of BitVectors must be positive')

        if not getattr(cls._size, '__isabstractmethod__', False):
            raise TypeError('Cannot generate sized from sized')


        if cls is AbstractBitVector:
            bases = (cls,)
        else:
            bases = (cls, AbstractBitVector[idx])

        class_name = '{}[{}]'.format(cls.__name__, idx)
        def size(self):
            return idx
        t = type(cls)(class_name, bases, {'_size' : size})
        t.__module__ = cls.__module__
        AbstractBitVectorMeta._class_cache[cls, idx] = t
        return t

class AbstractBitVector(metaclass=AbstractBitVectorMeta):
    def __new__(cls, value):
        if not getattr(cls._size, '__isabstractmethod__', False) or not hasattr(value, '__int__'):
            return super().__new__(cls)

        size = int(value).bit_length()
        return cls[size].__new__(cls[size], value)

    @abstractmethod
    def _size(self):
        pass

    @property
    def size(self):
        return self._size()

    @abstractmethod
    def __init__(self):
        pass

    @property
    def size(self):
        return self._size()


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
