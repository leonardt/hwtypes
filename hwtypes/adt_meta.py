import itertools as it
import typing as tp
from abc import ABCMeta, abstractmethod
import weakref

from types import MappingProxyType
from collections.abc import Mapping, MutableMapping
from collections import OrderedDict
from .util import TypedProperty
from .util import OrderedFrozenDict
from .util import _issubclass

__all__ = ['BoundMeta', 'TupleMeta', 'ProductMeta', 'SumMeta', 'EnumMeta']


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

RESERVED_NAMES = frozenset({
    'enumerate',
    'fields',
    'field_dict',
    'is_bound',
    'is_cached',
    'value',
    'value_dict',
})

RESERVED_SUNDERS = frozenset({
    '_cached_',
    '_fields_',
    '_field_table_',
    '_unbound_base_',
})

RESERVED_ATTRS = frozenset(RESERVED_NAMES | RESERVED_SUNDERS)

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
        for rname in RESERVED_SUNDERS:
            if rname in namespace:
                raise ReservedNameError(f'class attribute {rname} is reserved by the type machinery')

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

        t = super().__new__(mcs, name, bases, namespace, **kwargs)
        t._fields_ = bound_types
        t._unbound_base_ = None

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

    def _name_cb(cls, idx):
        '''
        Gives subclasses a chance define their name based on their idx.
        '''
        return '{}[{}]'.format(cls.__name__, ', '.join(map(lambda t : t.__name__, idx)))

    def __getitem__(cls, idx) -> 'BoundMeta':
        mcs = type(cls)
        if not isinstance(idx, tp.Iterable):
            idx = idx,

        idx = cls._fields_cb(idx)

        try:
            return mcs._class_cache[cls, idx]
        except KeyError:
            pass

        if cls.is_bound:
            raise TypeError('Type is already bound')

        bases = [cls]
        bases.extend(b[idx] for b in cls.__bases__ if isinstance(b, BoundMeta))
        bases = tuple(bases)
        class_name = cls._name_cb(idx)

        t = mcs(class_name, bases, {'__module__' : cls.__module__}, fields=idx)
        mcs._class_cache[cls, idx] = t
        t._cached_ = True
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

    def rebind(cls, A: type, B: type, rebind_sub_types: bool = False):
        new_fields = []
        for T in cls.fields:
            if T == A or (rebind_sub_types and _issubclass(T,A)):
                new_fields.append(B)
            elif isinstance(T, BoundMeta):
                new_fields.append(T.rebind(A, B, rebind_sub_types))
            else:
                new_fields.append(T)
        return cls.unbound_t[new_fields]

    @property
    def is_cached(cls):
        return getattr(cls, '_cached_', False)

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


class ProductMeta(TupleMeta):
    def __new__(mcs, name, bases, namespace, cache=False, **kwargs):
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
            if k in RESERVED_SUNDERS:
                raise ReservedNameError(f'class attribute {k} is reserved by the type machinery')
            elif _is_dunder(k) or _is_sunder(k) or _is_descriptor(v):
                ns[k] = v
            elif k in RESERVED_NAMES:
                raise ReservedNameError(f'Field name {k} is resevsed by the type machinery')
            elif isinstance(v, type):
                if k in fields:
                    raise TypeError(f'Conflicting definitions of field {k}')
                else:
                    fields[k] = v
            else:
                ns[k] = v

        if fields:
            return mcs._from_fields(fields, name, bases, ns, cache, **kwargs)
        else:
            return super().__new__(mcs, name, bases, ns, **kwargs)

    def __init__(cls, name, bases, namespace, cache=False, **kwargs):
        return super().__init__(name, bases, namespace, **kwargs)

    @classmethod
    def _from_fields(mcs, fields, name, bases, ns, cache, **kwargs):
        if cache:
            ns_idx = set()
            for k,v in ns.items():
                if not _is_dunder(k):
                    ns_idx.add((k,v))

            fields_idx = tuple(map(tuple, fields.items()))
            cache_idx = (fields_idx,
                    bases,
                    name,
                    frozenset(ns_idx),
                    frozenset(kwargs.items()),)

            try:
                return mcs._class_cache[cache_idx]
            except KeyError:
                pass

        # not strictly necessary could iterative over class dict finding
        # TypedProperty to reconstruct _field_table_ but that seems bad
        field_table = dict()

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
            field_table[field_name] = field_type
            ns[field_name] = _make_prop(field_type, idx)


        # this is all really gross but I don't know how to do this cleanly
        # need to build t so I can call super() in new and init
        # need to exec to get proper signatures
        t = super().__new__(mcs, name, bases, ns, **kwargs)
        t._field_table_ = OrderedFrozenDict(field_table)
        t._cahced_ = cache
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

        if cache:
            mcs._class_cache[cache_idx] = t

        return t


    def __getitem__(cls, idx):
        if cls.is_bound:
            return cls.fields[idx]
        else:
            raise TypeError("Cannot bind product types with getitem")

    @property
    def field_dict(cls):
        return MappingProxyType(cls._field_table_)

    def from_fields(cls,
            name: str,
            fields: tp.Mapping[str, type],
            cache: tp.Optional[bool] = None):

        if cls.is_bound:
            raise TypeError('Type must not be bound')

        for field in fields:
            if field in RESERVED_ATTRS:
                raise ReservedNameError(f'Field name {field} is reserved by the type machinery')

        ns = {}

        if cache is None:
            cache = True


        ns['__module__'] = cls.__module__
        ns['__qualname__'] = name

        return cls._from_fields(fields, name, (cls,), ns, cache)


    def rebind(cls, A: type, B: type, rebind_sub_types: bool = False):
        new_fields = OrderedDict()
        for field, T in cls.field_dict.items():
            if T == A or (rebind_sub_types and _issubclass(T,A)):
                new_fields[field] = B
            elif isinstance(T, BoundMeta):
                new_fields[field] = T.rebind(A, B, rebind_sub_types)
            else:
                new_fields[field] = T

        if new_fields != cls.field_dict:
            return cls.unbound_t.from_fields(cls.__name__, new_fields, cache=cls.is_cached)
        else:
            return cls

class SumMeta(BoundMeta):
    def __new__(mcs, name, bases, namespace, fields=None, **kwargs):
        def _make_prop(field_type):
            @TypedProperty(field_type)
            def prop(self):
                return self.value_dict[field_type.__name__]

            @prop.setter
            def prop(self, value):
                self.value = value

            return prop

        if fields is not None:
            for field in fields:
                fname = field.__name__
                if fname in RESERVED_ATTRS:
                    raise ReservedNameError(f'Field name {fname} is reserved by the type machinery')
                elif fname in namespace:
                    raise TypeError(f'Field name {fname} cannot be used as a class attribute')
                namespace[fname] = _make_prop(field)

        return super().__new__(mcs, name, bases, namespace, fields, **kwargs)

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
        elems = {}
        ns = {}

        for k, v in namespace.items():
            if k in RESERVED_SUNDERS:
                raise ReservedNameError(f'class attribute {k} is reserved by the type machinery')
            elif _is_dunder(k) or _is_sunder(k) or _is_descriptor(v):
                ns[k] = v
            elif k in RESERVED_NAMES:
                raise ReservedNameError(f'Field name {k} is resevsed by the type machinery')
            elif isinstance(v,  (int, mcs.Auto)):
                elems[k] = v
            else:
                raise TypeError(f'Enum value should be int not {type(v)}')

        t = super().__new__(mcs, cls_name, bases, ns, **kwargs)
        name_table = dict()

        if not elems:
            return t

        for name, value in elems.items():
            elem = t.__new__(t)
            t.__init__(elem, value)
            setattr(elem, '_name_', name)
            name_table[name] = elem
            setattr(t, name, elem)

        t._fields_ = tuple(name_table.values())
        t._field_table_ = name_table

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

    def rebind(cls, A: type, B: type, rebind_sub_types: bool = False):
        # Enums aren't bound to types
        # could potentialy rebind values but that seems annoying
        return cls
