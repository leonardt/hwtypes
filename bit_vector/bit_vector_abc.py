from abc import ABCMeta, abstractmethod
import typing as tp

class BitVectorABC(metaclass=ABCMeta):

    @abstractmethod
    def make_constant(self, value, num_bits:tp.Optional[int]=None):
        pass

    @abstractmethod
    def __getitem__(self, index):
        pass

    @abstractmethod
    def __setitem__(self, index, value):
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
