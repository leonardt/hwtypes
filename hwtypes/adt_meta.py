import itertools as it
import typing as tp
from abc import ABCMeta, abstractmethod
from collections import OrderedDict

import weakref

from types import MappingProxyType
from collections.abc import Mapping, MutableMapping
from .util import TypedProperty

__all__ = ['BoundMeta', 'TupleMeta', 'ProductMeta', 'SumMeta', 'EnumMeta']


def _issubclass(sub : tp.Any, parent : type) -> bool:
    try:
        return issubclass(sub, parent)
    except TypeError:
        return False


def _is_dunder(name):
    return (len(name) > 4
            and name[:2] == name[-2:] == '__'
            and name[2] != '_' and name[-3] != '_')


def _is_sunder(name):
    return (len(name) > 2
            and name[0] == name[-1] == '_'
            and name[1] != '_' and name[-2] != '_')


def _is_descriptor(obj):
    return hasattr(obj, '__get__') or hasattr(obj, '__set__') or hasattr(obj, '__delete__')


def is_adt_type(t):
    return isinstance(t, BoundMeta)


class ReservedNameError(Exception): pass

# Can't have abstract metaclass https://bugs.python.org/issue36881
class BoundMeta(type): #, metaclass=ABCMeta):
    # (UnboundType, (types...)) : BoundType
    _class_cache = weakref.WeakValueDictionary()

    def __call__(cls, *args, **kwargs):
        if not cls.is_bound:
            obj = cls.__new__(cls, *args, **kwargs)
            if not type(obj).is_bound:
                raise TypeError('Cannot instance unbound type')
            if isinstance(obj, cls):
                obj.__init__(*args, **kwargs)
            return obj
        else:
            obj = cls.__new__(cls, *args, **kwargs)
            if isinstance(obj, cls):
                obj.__init__(*args, **kwargs)
            return obj
        return super().__call__(*args, **kwargs)

    def __new__(mcs, name, bases, namespace, fields=None, **kwargs):
        if '_fields_' in namespace:
            raise ReservedNameError('class attribute _fields_ is reserved by the type machinery')
        if '_unbound_base_' in namespace:
            raise ReservedNameError('class attribute _unbound_base_ is reserved by the type machinery')

        bound_types = fields
        has_bound_base = False
        unbound_bases = []
        for base in bases:
            if isinstance(base, BoundMeta):
                if base.is_bound:
                    has_bound_base = True
                    if bound_types is None:
                        bound_types = base.fields
                    elif bound_types != base.fields:
                        raise TypeError("Can't inherit from multiple different bound_types")
                else:
                    unbound_bases.append(base)

        if bound_types is not None:
            if '_fields_cb' in namespace:
                bound_types  = namespace['_fields_cb'](bound_types)
            else:
                for t in bases:
                    if hasattr(t, '_fields_cb'):
                        bound_types = t._fields_cb(bound_types)

        namespace['_fields_'] = bound_types
        namespace['_unbound_base_'] = None
        t = super().__new__(mcs, name, bases, namespace, **kwargs)

        if bound_types is None:
            # t is a unbound type
            t._unbound_base_ = t
        elif len(unbound_bases) == 1:
            # t is constructed from an unbound type
            t._unbound_base_ = unbound_bases[0]
        elif not has_bound_base:
            # this shouldn't be reachable
            raise AssertionError("Unreachable code")

        return t

    def _fields_cb(cls, idx):
        '''
        Gives subclasses a chance to transform their fields. Before being bound.
        Major usecase being Sum is bound to frozenset of fields instead of a tuple
        '''
        return tuple(idx)

    def __getitem__(cls, idx) -> 'BoundMeta':
        if not isinstance(idx, tp.Iterable):
            idx = idx,

        idx = cls._fields_cb(idx)

        try:
            return BoundMeta._class_cache[cls, idx]
        except KeyError:
            pass

        if cls.is_bound:
            raise TypeError('Type is already bound')

        bases = [cls]
        bases.extend(b[idx] for b in cls.__bases__ if isinstance(b, BoundMeta))
        bases = tuple(bases)
        class_name = '{}[{}]'.format(cls.__name__, ', '.join(map(lambda t : t.__name__, idx)))
        t = type(cls)(class_name, bases, {}, fields=idx)
        t.__module__ = cls.__module__
        BoundMeta._class_cache[cls, idx] = t
        return t

    @property
    def fields(cls):
        return cls._fields_

    @property
    @abstractmethod
    def fields_dict(cls):
        pass

    @property
    def is_bound(cls) -> bool:
        return cls.fields is not None

    @property
    def unbound_t(cls) -> 'BoundMeta':
        t = cls._unbound_base_
        if t is not None:
            return t
        else:
            raise AttributeError(f'type {cls} has no unbound_t')

    def __repr__(cls):
        return f"{cls.__name__}"

    def rebind(cls, A : type, B : type):
        new_fields = []
        for T in cls.fields:
            if T == A:
                new_fields.append(B)
            elif isinstance(T, BoundMeta):
                new_fields.append(T.rebind(A, B))
            else:
                new_fields.append(T)
        return cls.unbound_t[new_fields]

class TupleMeta(BoundMeta):
    def __getitem__(cls, idx):
        if cls.is_bound:
            return cls.fields[idx]
        else:
            return super().__getitem__(idx)

    def enumerate(cls):
        field_iters = []
        for field in cls.fields:
            if isinstance(field, BoundMeta):
                field_iters.append(field.enumerate())
            else:
                field_iters.append((field(0),))

        for args in it.product(*field_iters):
            yield cls(*args)

    @property
    def field_dict(cls):
        return MappingProxyType({idx : field for idx, field in enumerate(cls.fields)})

_RESERVED_NAMES = {'enumerate', 'fields', 'field_dict', 'is_bound', 'value', 'value_dict'}
class ProductMeta(TupleMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        fields = {}
        ns = {}
        for base in bases:
            if base.is_bound:
                for k,v in base.field_dict.items():
                    if k in fields:
                        raise TypeError(f'Conflicting definitions of field {k}')
                    else:
                        fields[k] = v
        for k, v in namespace.items():
            if _is_sunder(k) or _is_dunder(k) or _is_descriptor(v):
                ns[k] = v
            elif isinstance(v, type):
                if k in fields:
                    raise TypeError(f'Conflicting definitions of field {k}')
                else:
                    fields[k] = v
            else:
                ns[k] = v

        if fields:
            return mcs._from_fields(fields, name, bases, ns,  **kwargs)
        else:
            return super().__new__(mcs, name, bases, ns, **kwargs)

    @classmethod
    def _from_fields(mcs, fields, name, bases, ns, **kwargs):
        # not strictly necessary could iterative over class dict finding
        # TypedProperty to reconstruct _field_table_ but that seems bad
        if '_field_table_' in ns:
            raise ReservedNameError('class attribute _field_table_ is reserved by the type machinery')
        else:
            ns['_field_table_'] = OrderedDict()

        for field in fields:
            if field in _RESERVED_NAMES:
                raise ReservedNameError(f'Field name {field} is reserved by the type machinery')

        def _get_tuple_base(bases):
            for base in bases:
                if not isinstance(base, ProductMeta) and isinstance(base, TupleMeta):
                    return base
                r_base =_get_tuple_base(base.__bases__)
                if r_base is not None:
                    return r_base
            return None

        base = _get_tuple_base(bases)[tuple(fields.values())]
        bases = *bases, base

        # field_name -> tuple index
        idx_table = dict((k, i) for i,k in enumerate(fields.keys()))

        def _make_prop(field_type, idx):
            @TypedProperty(field_type)
            def prop(self):
                return self[idx]

            @prop.setter
            def prop(self, value):
                self[idx] = value

            return prop

        # add properties to namespace
        # build properties
        for field_name, field_type in fields.items():
            assert field_name not in ns
            idx = idx_table[field_name]
            ns['_field_table_'][field_name] = field_type
            ns[field_name] = _make_prop(field_type, idx)

        # this is all really gross but I don't know how to do this cleanly
        # need to build t so I can call super() in new and init
        # need to exec to get proper signatures
        t = super().__new__(mcs, name, bases, ns, **kwargs)
        gs = {name : t, 'ProductMeta' : ProductMeta}
        ls = {}

        arg_list = ','.join(fields.keys())
        type_sig = ','.join(f'{k}: {v.__name__!r}' for k,v in fields.items())

        # build __new__
        __new__ = f'''
def __new__(cls, {type_sig}):
    return super({name}, cls).__new__(cls, {arg_list})
'''
        exec(__new__, gs, ls)
        t.__new__ = ls['__new__']

        # build __init__
        __init__ = f'''
def __init__(self, {type_sig}):
    return super({name}, self).__init__({arg_list})
'''
        exec(__init__, gs, ls)
        t.__init__ = ls['__init__']

        product_base = None
        for base in bases:
            if isinstance(base, mcs):
                if product_base is None:
                    product_base = base
                else:
                    raise TypeError('Can only inherit from one product type')

        if product_base is not None and not product_base.is_bound:
            t._unbound_base_ = product_base

        return t


    def __getitem__(cls, idx):
        if cls.is_bound:
            return cls.fields[idx]
        else:
            raise TypeError("Cannot bind product types with getitem")

    def __repr__(cls):
        if cls.is_bound:
            field_spec = ', '.join(map('{0[0]}={0[1].__name__}'.format, cls.field_dict.items()))
            return f"{cls.__bases__[0].__name__}('{cls.__name__}', {field_spec})"
        else:
            return super().__repr__()

    @property
    def field_dict(cls):
        return MappingProxyType(cls._field_table_)

    def from_fields(cls,
            class_name: str,
            fields: tp.Mapping[str, type],
            module: tp.Optional[str] = None,
            qualname: tp.Optional[str] = None):
        if cls.is_bound:
            raise TypeError('Type must not be bound')

        ns = {}

        if module is None:
            module = cls.__module__

        if qualname is None:
            qualname = class_name

        ns['__module__'] = module
        ns['__qualname__'] = qualname

        return cls._from_fields(fields, class_name, (cls,), ns)


    def rebind(cls, A : type, B : type):
        new_fields = OrderedDict()
        for field, T in cls.field_dict.items():
            if T == A:
                new_fields[field] = B
            elif isinstance(T, BoundMeta):
                new_fields[field] = T.rebind(A, B)
            else:
                new_fields[field] = T
        return cls.unbound_t.from_fields(cls.__name__, new_fields, cls.__module__, cls.__qualname__)

class SumMeta(BoundMeta):
    def _fields_cb(cls, idx):
        return frozenset(idx)

    def enumerate(cls):
        for field in cls.fields:
            if isinstance(field, BoundMeta):
                yield from map(cls, field.enumerate())
            else:
                yield cls(field())

    @property
    def field_dict(cls):
        return MappingProxyType({field.__name__ : field for field in cls.fields})


class EnumMeta(BoundMeta):
    class Auto:
        def __repr__(self):
            return 'Auto()'

    def __new__(mcs, cls_name, bases, namespace, **kwargs):
        if '_field_table_' in namespace:
            raise ReservedNameError('class attribute _field_table_ is reserved by the type machinery')

        elems = {}
        ns = {}

        for k, v in namespace.items():
            if _is_dunder(k) or _is_sunder(k) or _is_descriptor(v):
                ns[k] = v
            elif k in _RESERVED_NAMES:
                raise ReservedNameError(f'Field name {k} is resevsed by the type machinery')
            elif isinstance(v,  (int, mcs.Auto)):
                elems[k] = v
            else:
                raise TypeError(f'Enum value should be int not {type(v)}')

        ns['_field_table_'] = name_table = dict()
        t = super().__new__(mcs, cls_name, bases, ns, **kwargs)

        if not elems:
            return t

        for name, value in elems.items():
            elem = t.__new__(t)
            elem.__init__(value)
            setattr(elem, '_name_', name)
            name_table[name] = elem
            setattr(t, name, elem)

        t._fields_ = tuple(name_table.values())

        enum_base = None
        for base in bases:
            if isinstance(base, mcs):
                if enum_base is None:
                    enum_base = base
                else:
                    raise TypeError('Can only inherit from one enum type')

        if enum_base is not None:
            t._unbound_base_ = enum_base

        return t

    def __call__(cls, elem):
        if not isinstance(elem, cls):
            raise TypeError('Enums cannot be constructed by value')
        return elem

    @property
    def field_dict(cls):
        return MappingProxyType(cls._field_table_)

    def enumerate(cls):
        yield from cls.fields

    def rebind(cls, A : type, B : type):
        # Enums aren't bound to types
        # could potentialy rebind values but that seems annoying
        return cls
