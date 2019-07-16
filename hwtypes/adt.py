from .adt_meta import TupleMeta, ProductMeta, SumMeta, EnumMeta, is_adt_type
from collections import OrderedDict
from types import MappingProxyType
import typing as tp

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

        self._value = value

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.value == other.value
        else:
            return NotImplemented

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.value)

    def __getitem__(self, idx):
        return self.value[idx]

    def __setitem__(self, idx, value):
        if isinstance(value, type(self)[idx]):
            v = list(self.value)
            v[idx] = value
            self._value = v
        else:
            raise TypeError(f'Value {value} is not of type {type(self)[idx]}')

    @property
    def value(self):
        return self._value

    def __repr__(self):
        return f'{type(self).__name__}({", ".join(map(repr, self.value))})'

    @property
    def value_dict(self):
        d = {}
        for k in type(self).field_dict:
            d[k] = self[k]
        return MappingProxyType(d)


class Product(Tuple, metaclass=ProductMeta):
    def __repr__(self):
        return f'{type(self).__name__}({", ".join(f"{k}={v}" for k,v in self.value_dict.items())})'

    @property
    def value_dict(self):
        d = OrderedDict()
        for k in type(self).field_dict:
            d[k] = getattr(self, k)
        return MappingProxyType(d)

class Sum(metaclass=SumMeta):
    def __init__(self, value):
        if not isinstance(value, tuple(type(self).fields)):
            raise TypeError(f'Value {value} is not of types {type(self).fields}')
        self._value = value

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.value == other.value

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.value)

    @property
    def value(self):
        return self._value

    def match(self):
        return type(self.value), self.value

    def __repr__(self) -> str:
        return f'{type(self)}({self.value})'

    @property
    def value_dict(self):
        d = {}
        for k,t in type(self).field_dict.items():
            if isinstance(self.value, t):
                d[k] = self.value
            else:
                d[k] = None
        return MappingProxyType(d)

class Enum(metaclass=EnumMeta):
    def __init__(self, value):
        self._value_ = value

    @property
    def value(self):
        return self._value_

    @property
    def name(self):
        return self._name_

    def __repr__(self):
        return f'{type(self).__name__}.{self.name}'

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.value == other.value

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.value)

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

def new_instruction():
    return EnumMeta.Auto()
