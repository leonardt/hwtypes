from abc import ABCMeta, abstractmethod
import typing as tp
import weakref
import warnings
from enum import Enum, auto

from . import AbstractBitVectorMeta, AbstractBitVector, AbstractBit

class RoundingMode(Enum):
    RNE = auto() # roundTiesToEven
    RNA = auto() # roundTiesToAway
    RTP = auto() # roundTowardPositive
    RTN = auto() # roundTowardNegative
    RTZ = auto() # roundTowardZero

class AbstractFPVectorMeta(ABCMeta):
    # FPVectorType, (eb, mb, mode, ieee_compliance) :  FPVectorType[eb, mb, mode, ieee_compliance]
    _class_cache = weakref.WeakValueDictionary()

    # FPVectorType : UnsizedFPVectorType, (eb, mb, mode ,ieee_compliance)
    _class_info  = weakref.WeakKeyDictionary()

    def __new__(mcs, name, bases, namespace, **kwargs):
        info = None
        for base in bases:
            if getattr(base, 'is_bound', False):
                if info is None:
                    info = base.info
                elif info != base.info:
                    raise TypeError("Can't inherit from multiple FP types")
        t = super().__new__(mcs, name, bases, namespace, **kwargs)
        if info is None:
            mcs._class_info[t] = t, info
        else:
            mcs._class_info[t] = None, info

        return t

    def __getitem__(cls, idx : tp.Tuple[int, int, RoundingMode, bool]):
        mcs = type(cls)
        try:
            return mcs._class_cache[cls, idx]
        except KeyError:
            pass

        if cls.is_bound:
            raise TypeError(f'{cls} is already bound')

        if len(idx) != 4 or tuple(map(type,idx)) != (int, int, RoundingMode, bool):
            raise IndexError(f'Constructing a floating point type requires:\n'
                    'exponent bits : int, mantisa bits : int, RoundingMode, ieee_compliance : bool')

        eb, mb, mode, ieee_compliance = idx

        if eb <= 0 or mb <= 0:
            raise ValueError('exponents bits and mantisa bits must be greater than 0')


        bases = [cls]
        bases.extend(b[idx] for b in cls.__bases__ if isinstance(b, AbstractFPVectorMeta))
        bases = tuple(bases)
        class_name = f'{cls.__name__}[{eb},{mb},{mode},{ieee_compliance}]'
        t = mcs(class_name, bases, {})
        t.__module__ = cls.__module__
        mcs._class_cache[cls, idx] = t
        mcs._class_info[t] = cls, idx

        return t

    @property
    def unbound_t(cls) -> 'AbstractBitVectorMeta':
        t = type(cls)._class_info[cls][0]
        if t is not None:
            return t
        else:
            raise AttributeError('type {} has no unsized_t'.format(cls))

    @property
    def size(cls):
        return 1 + cls.exponent_size + cls.mantissa_size

    @property
    def is_bound(cls):
        return cls.info is not None

    @property
    def info(cls):
        return type(cls)._class_info[cls][1]

    @property
    def exponent_size(cls):
        return cls.info[0]

    @property
    def mantissa_size(cls):
        return cls.info[1]

    @property
    def mode(cls) -> RoundingMode:
        return cls.info[2]

    @property
    def ieee_compliance(cls) -> bool:
        return cls.info[3]

class AbstractFPVector(metaclass=AbstractFPVectorMeta):
    @property
    def size(self) -> int:
        return  type(self).size

    @abstractmethod
    def fp_abs(self) -> 'AbstractFPVector': pass

    @abstractmethod
    def fp_neg(self) -> 'AbstractFPVector': pass

    @abstractmethod
    def fp_add(self, other: 'AbstractFPVector') -> 'AbstractFPVector': pass

    @abstractmethod
    def fp_sub(self, other: 'AbstractFPVector') -> 'AbstractFPVector': pass

    @abstractmethod
    def fp_mul(self, other: 'AbstractFPVector') -> 'AbstractFPVector': pass

    @abstractmethod
    def fp_div(self, other: 'AbstractFPVector') -> 'AbstractFPVector': pass

    @abstractmethod
    def fp_fma(self, coef: 'AbstractFPVector', offset: 'AbstractFPVector') -> 'AbstractFPVector': pass

    @abstractmethod
    def fp_sqrt(self) -> 'AbstractFPVector': pass

    @abstractmethod
    def fp_rem(self, other: 'AbstractFPVector') -> 'AbstractFPVector': pass

    @abstractmethod
    def fp_round_to_integral(self) -> 'AbstractFPVector': pass

    @abstractmethod
    def fp_min(self, other: 'AbstractFPVector') -> 'AbstractFPVector': pass

    @abstractmethod
    def fp_max(self, other: 'AbstractFPVector') -> 'AbstractFPVector': pass

    @abstractmethod
    def fp_leq(self, other: 'AbstractFPVector') ->  AbstractBit: pass

    @abstractmethod
    def fp_lt(self, other: 'AbstractFPVector') ->  AbstractBit: pass

    @abstractmethod
    def fp_geq(self, other: 'AbstractFPVector') ->  AbstractBit: pass

    @abstractmethod
    def fp_gt(self, other: 'AbstractFPVector') ->  AbstractBit: pass

    @abstractmethod
    def fp_eq(self, other: 'AbstractFPVector') ->  AbstractBit: pass

    @abstractmethod
    def fp_is_normal(self) -> AbstractBit: pass

    @abstractmethod
    def fp_is_subnormal(self) -> AbstractBit: pass

    @abstractmethod
    def fp_is_zero(self) -> AbstractBit: pass

    @abstractmethod
    def fp_is_infinite(self) -> AbstractBit: pass

    @abstractmethod
    def fp_is_NaN(self) -> AbstractBit: pass

    @abstractmethod
    def fp_is_negative(self) -> AbstractBit: pass

    @abstractmethod
    def fp_is_positive(self) -> AbstractBit: pass

    @abstractmethod
    def to_ubv(self, size : int) -> AbstractBitVector: pass

    @abstractmethod
    def to_sbv(self, size : int) -> AbstractBitVector: pass

    @abstractmethod
    def reinterpret_as_bv(self) -> AbstractBitVector: pass

    @classmethod
    @abstractmethod
    def reinterpret_from_bv(self, value: AbstractBitVector) -> 'AbstractFPVector': pass
