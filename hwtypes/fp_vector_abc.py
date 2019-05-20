from abc import ABCMeta, abstractmethod
import typing as tp
import weakref
import warnings
import enum

from . import AbstractBitVectorMeta, AbstractBitVector, AbstractBit

class RoundingMode(enum.Enum):
    RNE = enum.auto() # roundTiesToEven
    RNA = enum.auto() # roundTiesToAway
    RTP = enum.auto() # roundTowardPositive
    RTN = enum.auto() # roundTowardNegative
    RTZ = enum.auto() # roundTowardZero

class AbstractFPVectorMeta(ABCMeta):
    # FPVectorType, (eb, mb, mode, ieee_compliance) :  FPVectorType[eb, mb, mode, ieee_compliance]
    _class_cache = weakref.WeakValueDictionary()

    def __new__(mcs, name, bases, namespace, info=(None, None), **kwargs):
        if '_info_' in namespace:
            raise TypeError('class attribute _info_ is reversed by the type machinery')

        binding = info[1]
        for base in bases:
            if getattr(base, 'is_bound', False):
                if binding is None:
                    binding = base.binding
                elif binding != base.binding:
                    raise TypeError("Can't inherit from multiple FP types")

        namespace['_info_'] = info[0], binding
        t = super().__new__(mcs, name, bases, namespace, **kwargs)

        if binding is None:
            #class is unbound so t.unbound_t -> t
            t._info_ = t, binding
        elif info[0] is None:
            #class inherited from bound type so there is no unbound_t
            t._info_ = None, binding

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
        t = mcs(class_name, bases, {}, info=(cls, idx))
        t.__module__ = cls.__module__
        mcs._class_cache[cls, idx] = t
        return t

    @property
    def unbound_t(cls) -> 'AbstractBitVectorMeta':
        t = cls._info_[0]
        if t is not None:
            return t
        else:
            raise AttributeError('type {} has no unsized_t'.format(cls))

    @property
    def size(cls):
        return 1 + cls.exponent_size + cls.mantissa_size

    @property
    def is_bound(cls):
        return cls.binding is not None

    @property
    def binding(cls):
        return cls._info_[1]

    @property
    def exponent_size(cls):
        if cls.is_bound:
            return cls.binding[0]
        else:
            raise AttributeError('unbound type has no exponent_size')

    @property
    def mantissa_size(cls):
        if cls.is_bound:
            return cls.binding[1]
        else:
            raise AttributeError('unbound type has no mantissa_size')

    @property
    def mode(cls) -> RoundingMode:
        if cls.is_bound:
            return cls.binding[2]
        else:
            raise AttributeError('unbound type has no mode')

    @property
    def ieee_compliance(cls) -> bool:
        if cls.is_bound:
            return cls.binding[3]
        else:
            raise AttributeError('unbound type has no ieee_compliance')

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
