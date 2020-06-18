from collections import OrderedDict
from types import MappingProxyType
import typing as tp
import warnings

from .adt_meta import TupleMeta, AnonymousProductMeta, ProductMeta
from .adt_meta import SumMeta, TaggedUnionMeta, EnumMeta, is_adt_type

__all__  = ['Tuple', 'Product', 'Sum', 'Enum']
__all__ += ['new_instruction', 'is_adt_type']

#special sentinal value
class _MISSING: pass

class Tuple(metaclass=TupleMeta):
    def __new__(cls, *value):
        if cls.is_bound:
            return super().__new__(cls)
        else:
            idx = tuple(type(v) for v in value)
            return cls[idx].__new__(cls[idx], *value)

    def __init__(self, *value):
        cls = type(self)
        if len(value) != len(cls.fields):
            raise ValueError('Incorrect number of arguments')
        for v,t in zip(value, cls.fields):
            if not isinstance(v,t):
                raise TypeError('Value {} is not of type {}'.format(repr(v), repr(t)))

        self._value_ = value

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._value_ == other._value_
        else:
            return NotImplemented

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self._value_)

    def __getitem__(self, idx):
        return self._value_[idx]

    def __setitem__(self, idx, value):
        if isinstance(value, type(self)[idx]):
            v = list(self._value_)
            v[idx] = value
            self._value_ = v
        else:
            raise TypeError(f'Value {value} is not of type {type(self)[idx]}')

    def __repr__(self):
        return f'{type(self).__name__}({", ".join(map(repr, self._value_))})'

    @property
    def value_dict(self):
        d = {}
        for k in type(self).field_dict:
            d[k] = self[k]
        return MappingProxyType(d)

    @classmethod
    def from_values(cls, value_dict):
        if value_dict.keys() != cls.field_dict.keys():
            raise ValueError('Keys do not match field_dict')

        for k, v in value_dict.items():
            if not isinstance(v, cls.field_dict[k]):
                raise TypeError(f'Expected object of type {cls.field_dict[k]}'
                                f' got {v}')


        # So Product can use the type checking logic above
        return cls._from_kwargs(value_dict)


    @classmethod
    def _from_kwargs(cls, kwargs):
        args = [None]*len(kwargs)
        for k, v in kwargs.items():
            args[k] = v

        return cls(*args)

    @property
    def value(self):
        warnings.warn('DEPRECATION WARNING: ADT.value is deprecated', DeprecationWarning, 2)
        return self._value_

class AnonymousProduct(Tuple, metaclass=AnonymousProductMeta):
    def __repr__(self):
        return f'{type(self).__name__}({", ".join(f"{k}={v}" for k,v in self.value_dict.items())})'

    @property
    def value_dict(self):
        d = OrderedDict()
        for k in type(self).field_dict:
            d[k] = getattr(self, k)
        return MappingProxyType(d)

    @classmethod
    def _from_kwargs(cls, kwargs):
        return cls(**kwargs)


class Product(AnonymousProduct, metaclass=ProductMeta):
    pass

class Sum(metaclass=SumMeta):
    class Match:
        __slots__ = ('_match', '_value', '_safe')
        def __init__(self, match, value, *, safe: bool = True):
            self._match = match
            self._value = value
            self._safe = safe

        @property
        def match(self):
            return self._match

        @property
        def value(self):
            if not self._safe or self.match:
                return self._value
            else:
                raise TypeError(f'No value for unmatched type')

    def __init__(self, value):
        if type(value) not in type(self):
            raise TypeError(f'Value {value} is not of types {type(self).fields}')
        self._value_ = value

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._value_ == other._value_
        else:
            return NotImplemented

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self._value_)

    def __getitem__(self, T) -> 'Sum.Match':
        cls = type(self)
        if T in cls:
            return cls.Match(isinstance(self._value_, T), self._value_)
        else:
            raise TypeError(f'{T} not in {cls}')


    def __setitem__(self, T, value):
        if T not in type(self):
            raise TypeError(f'indices must be in {type(self).fields} not {T}')
        elif not isinstance(value, T):
            raise TypeError(f'expected {T} not {type(value)}')
        else:
            self._value_ = value

    def __repr__(self) -> str:
        return f'{type(self)}({self._value_})'

    @property
    def value_dict(self):
        d = {}
        for k,t in type(self).field_dict.items():
            if self[t].match:
                d[k] = self._value_
            else:
                d[k] = None
        return MappingProxyType(d)

    @classmethod
    def from_values(cls, value_dict):
        if value_dict.keys() != cls.field_dict.keys():
            raise ValueError('Keys do not match field_dict')

        kwargs = {}
        for k, v in value_dict.items():
            if v is not None and not isinstance(v, cls.field_dict[k]):
                raise TypeError(f'Expected object of type {cls.field_dict[k]}'
                                f' got {v}')
            elif v is not None:
                kwargs[k] = v

        if not len(kwargs) == 1:
            raise ValueError(f'value_dict must have exactly one non None entry')

        # So TaggedUnion can use the type checking logic above
        return cls._from_kwargs(kwargs)

    @classmethod
    def _from_kwargs(cls, kwargs):
        assert len(kwargs) == 1
        _, v = kwargs.popitem()
        return cls(v)

    @property
    def value(self):
        warnings.warn('DEPRECATION WARNING: ADT.value is deprecated', DeprecationWarning, 2)
        return self._value_


class TaggedUnion(Sum, metaclass=TaggedUnionMeta):
    def __init__(self, **kwargs):
        if len(kwargs) == 0:
            raise ValueError('Must specify a value')
        elif len(kwargs) != 1:
            raise ValueError('Expected one value')

        cls = type(self)
        field, value = next(iter(kwargs.items()))
        if field not in cls.field_dict:
            raise ValueError(f'Invalid field {field}')

        setattr(self, field, value)

    def __setitem__(self, T, value):
        raise TypeError(f'setitem syntax is not supported on {type(self)}')

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._tag_ == other._tag_ and self._value_ == other._value_
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self._tag_) + hash(self._value_)

    def __repr__(self):
        return f'{type(self).__name__}({", ".join(f"{k}={v}" for k,v in self.value_dict.items())})'

    @property
    def value_dict(self):
        d = dict()
        for k in type(self).field_dict:
            m = getattr(self, k)
            if m.match:
                d[k] = m.value
            else:
                d[k] = None
        return MappingProxyType(d)

    @classmethod
    def _from_kwargs(cls, kwargs):
        assert len(kwargs) == 1
        return cls(**kwargs)


class Enum(metaclass=EnumMeta):
    def __init__(self, value):
        self._value_ = value

    @property
    def name(self):
        return self._name_

    def __repr__(self):
        return f'{type(self).__name__}.{self.name}'

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self._value_ == other._value_
        else:
            return NotImplemented

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self._value_)

    def __getattribute__(self, attr):
        # prevent:
        #  class E(Enum):
        #   a = 0
        #   b = 1
        #  E.a.b == E.b
        if attr in type(self).field_dict:
            raise AttributeError('Cannot access enum members from enum instances')
        else:
            return super().__getattribute__(attr)

    @property
    def value(self):
        warnings.warn('DEPRECATION WARNING: ADT.value is deprecated', DeprecationWarning, 3)
        return self._value_

def new_instruction():
    return EnumMeta.Auto()
