from abc import ABCMeta, abstractmethod
import itertools as it
import typing as tp
import weakref

from types import MappingProxyType
from collections.abc import Mapping, MutableMapping
from collections import OrderedDict
from .util import TypedProperty
from .util import OrderedFrozenDict, FrozenDict
from .util import _issubclass

__all__ = [
    'BoundMeta', 'TupleMeta', 'ProductMeta',
    'SumMeta', 'TaggedUnionMeta', 'EnumMeta']


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
    'value_dict',
    'from_values',
})

RESERVED_SUNDERS = frozenset({
    '_value_',
    '_tag_',
    '_cached_',
    '_fields_',
    '_field_table_',
    '_unbound_base_',
    '_syntax_',
})

RESERVED_ATTRS = frozenset(RESERVED_NAMES | RESERVED_SUNDERS)

class Syntax(type):
    def __subclasscheck__(cls, sub):
        return super().__subclasscheck__(getattr(sub, '_syntax_', type(None)))

    def __instancecheck__(cls, instance):
        return cls.__subclasscheck__(type(instance))


class AttrSyntax(metaclass=Syntax): pass
class GetitemSyntax(metaclass=Syntax): pass

# Can't have abstract metaclass https://bugs.python.org/issue36881
class _GetitemSyntax(type): #(metaclass=ABCMeta):
    # Should probaly do more than it currently does but it gets the job done
    ORDERED = False
    _syntax_ = GetitemSyntax

    def __getitem__(cls, idx):
        idx = cls._get_idx(idx)
        return cls._cache_handler(idx)

    def _get_idx(cls, idx):
        '''
        Translates the index passed to __getitem__ into the index
        that will be used in the rest of type machinery
        '''
        if not isinstance(idx, tp.Iterable):
            idx = idx,

        if type(cls).ORDERED:
            idx = tuple(idx)
        else:
            idx = frozenset(idx)

        return idx

    def _cache_handler(cls, idx):
        mcs = type(cls)
        try:
            return mcs._class_cache[cls, idx]
        except KeyError:
            pass

        t = cls._from_idx(idx)
        mcs._class_cache[cls, idx] = t
        t._cached_ = True
        return t

    @abstractmethod
    def _from_idx(cls, idx):
        pass

    def rebind(cls, A: type, B: type, rebind_sub_types: bool = False, rebind_recursive: bool = True):
        new_fields = []
        for T in cls.fields:
            if T == A or (rebind_sub_types and _issubclass(T,A)):
                new_fields.append(B)
            elif rebind_recursive and isinstance(T, BoundMeta):
                new_fields.append(T.rebind(A, B, rebind_sub_types))
            else:
                new_fields.append(T)
        return cls.unbound_t[new_fields]



class _AttrSyntax(type): #, metaclass=ABCMeta):
    # Tells AttrSyntax which attrs are fields
    FIELDS_T = type
    ORDERED =  False
    _syntax_ = AttrSyntax

    def __new__(mcs, name, bases, namespace, cache=True, **kwargs):
        fields = {}
        ns = {}

        for k, v in namespace.items():
            if k in RESERVED_SUNDERS:
                raise ReservedNameError(f'class attribute {k} is reserved by the type machinery')
            elif _is_dunder(k) or _is_sunder(k) or _is_descriptor(v):
                ns[k] = v
            elif k in RESERVED_NAMES:
                raise ReservedNameError(f'Field name {k} is resevsed by the type machinery')
            elif isinstance(v, mcs.FIELDS_T):
                fields[k] = v
            else:
                ns[k] = v

        return mcs._cache_handler(cache, fields, name, bases, ns, **kwargs)

    @classmethod
    def _cache_handler(mcs, cache, fields, name, bases, ns, **kwargs):
        if fields:
            if cache:
                ns_idx = set()
                for k,v in ns.items():
                    if not _is_dunder(k):
                        ns_idx.add((k,v))

                if mcs.ORDERED:
                    fields_idx = tuple(map(tuple, fields.items()))
                else:
                    fields_idx = frozenset(map(tuple, fields.items()))

                cache_idx = (fields_idx,
                        bases,
                        name,
                        frozenset(ns_idx),
                        frozenset(kwargs.items()),)

                try:
                    return mcs._class_cache[cache_idx]
                except KeyError:
                    pass
            t = mcs._from_fields(fields, name, bases, ns, **kwargs)
            t._cached_ = cache
            if cache:
                mcs._class_cache[cache_idx] = t
            return t
        else:
            return super().__new__(mcs, name, bases, ns, **kwargs)

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

        return cls._cache_handler(cache, fields, name, (cls,), ns)

    @classmethod
    @abstractmethod
    def _from_fields(mcs, fields, name, bases, ns, **kwargs):
        pass

    def rebind(cls, A: type, B: type, rebind_sub_types: bool = False, rebind_recursive: bool = True):
        new_fields = OrderedDict()
        for field, T in cls.field_dict.items():
            if T == A or (rebind_sub_types and _issubclass(T,A)):
                new_fields[field] = B
            elif rebind_recursive and isinstance(T, BoundMeta):
                new_fields[field] = T.rebind(A, B, rebind_sub_types)
            else:
                new_fields[field] = T

        if new_fields != cls.field_dict:
            return cls.unbound_t.from_fields(cls.__name__, new_fields, cache=cls.is_cached)
        else:
            return cls


class BoundMeta(_GetitemSyntax): #, metaclass=ABCMeta):
    # for legacy reasons
    ORDERED = True

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

    def _from_idx(cls, idx) -> 'BoundMeta':
        mcs= type(cls)
        if cls.is_bound:
            raise TypeError('Type is already bound')

        # By using callbacks instead of making these arguments
        # and using a `if arg is None: arg = default_behavior` pattern
        # sub types can extend default_behavior
        class_name = cls._name_from_idx(idx)
        bases = cls._bases_from_idx(idx)
        fields = cls._fields_from_idx(idx)
        namespace = cls._namespace_from_idx(idx)

        t = mcs(class_name, bases, namespace, fields=fields)
        return t

    def _name_from_idx(cls, idx):
        '''
        Gives subclasses a chance define their name based on their idx.
        '''
        # for legacy reasons we dispacth to `_name_cb`
        # will be removed in future versions
        return cls._name_cb(idx)

    def _name_cb(cls, idx):
        return '{}[{}]'.format(cls.__name__, ', '.join(map(lambda t : t.__name__, idx)))

    def _bases_from_idx(cls, idx):
        bases = [cls]
        bases.extend(b[idx] for b in cls.__bases__ if isinstance(b, type(cls)))
        bases = tuple(bases)
        return bases

    def _fields_from_idx(cls, idx):
        return idx

    def _namespace_from_idx(cls, idx):
        return {'__module__' : cls.__module__}

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

    @property
    def is_cached(cls):
        return getattr(cls, '_cached_', False)


class TupleMeta(BoundMeta):
    ORDERED = True

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


class AnonymousProductMeta(TupleMeta):
    def _get_idx(cls, idx):
        if not isinstance(idx, tp.Mapping):
            raise TypeError()
        return OrderedFrozenDict(idx)

    def _from_idx(cls, idx):
        # need to build t so I can call super() in new and init
        #(hence cannot construct them in the namespace call back)
        # need to exec to get proper signatures
        # need proper sigatures so both:
        # Product_t(field=value, ...) and Product_t(value, ...) works
        t = super()._from_idx(idx)
        t._field_table_ = idx

        name =  t.unbound_t.__name__
        gs = {name : t}

        ls = {}

        arg_list = ','.join(idx.keys())
        type_sig = ','.join(f'{k}: {v.__name__!r}' for k,v in idx.items())

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
        return t


    def _bases_from_idx(cls, idx):
        mcs = type(cls)
        def _get_tuple_base(bases):
            for base in bases:
                if not isinstance(base, mcs) and isinstance(base, TupleMeta):
                    return base
                r_base =_get_tuple_base(base.__bases__)
                if r_base is not None:
                    return r_base
            return None
        bases = super()._bases_from_idx(idx)
        base = _get_tuple_base(bases)[tuple(idx.values())]
        return (*bases, base)

    def _name_from_idx(cls, idx):
        return '{}[{{{}}}]'.format(cls.__name__, ', '.join(f"'{k}': {t.__name__}" for k, t in idx.items()))

    def _fields_from_idx(cls, idx):
        return tuple(idx.values())

    def _namespace_from_idx(cls, idx):
        ns = super()._namespace_from_idx(idx)

        # field_name -> tuple index
        idx_table = dict((k, i) for i,k in enumerate(idx.keys()))

        def _make_prop(field_type, idx):
            @TypedProperty(field_type)
            def prop(self):
                return self[idx]

            @prop.setter
            def prop(self, value):
                self[idx] = value

            return prop

        # add properties to namespace
        for field_name, field_type in idx.items():
            assert field_name not in ns
            idx = idx_table[field_name]
            ns[field_name] = _make_prop(field_type, idx)

        return ns

    @property
    def field_dict(cls):
        return MappingProxyType(cls._field_table_)


class ProductMeta(_AttrSyntax, AnonymousProductMeta):
    FIELDS_T = type
    ORDERED = True

    @classmethod
    def _from_fields(mcs, fields, name, bases, ns, **kwargs):

        def _get_anon_base(bases):
            for base in bases:
                if not isinstance(base, mcs) and isinstance(base, AnonymousProductMeta):
                    return base
                r_base =_get_anon_base(base.__bases__)
                if r_base is not None:
                    return r_base
            return None
        base = _get_anon_base(bases)[fields]
        bases = *bases, base

        t = super().__new__(mcs, name, bases, ns, **kwargs)

        return t

    def __getitem__(cls, idx):
        if cls.is_bound:
            if isinstance(idx, str):
                return cls.field_dict[idx]
            else:
                return super().__getitem__(idx)
        else:
            raise TypeError("Cannot bind product types with getitem")


class SumMeta(BoundMeta):
    ORDERED = False

    def __getitem__(cls, T):
        if cls.is_bound:
            if T in cls:
                return T
            else:
                raise KeyError(f'{T} not in {cls}')
        else:
            return super().__getitem__(T)

    def __contains__(cls, T):
        return T in cls.fields

    def enumerate(cls):
        for field in cls.fields:
            if isinstance(field, BoundMeta):
                yield from map(cls, field.enumerate())
            else:
                yield cls(field())

    @property
    def field_dict(cls):
        return MappingProxyType({field : field for field in cls.fields})


class TaggedUnionMeta(_AttrSyntax, SumMeta):
    FIELDS_T = type
    ORDERED = False

    @classmethod
    def _from_fields(mcs, fields, name, bases, ns, **kwargs):
        def _get_sum_base(bases):
            for base in bases:
                if not isinstance(base, mcs) and isinstance(base, SumMeta):
                    return base
                r_base =_get_sum_base(base.__bases__)
                if r_base is not None:
                    return r_base
            return None

        sum_base = _get_sum_base(bases)[tuple(fields.values())]
        bases = *bases, sum_base

        def _make_prop(field_type, tag):
            @TypedProperty(field_type)
            def prop(self):
                cls = type(self)
                return cls.Match(self._tag_ == tag, self._value_)

            @prop.setter
            def prop(self, value):
                self._value_ = value
                self._tag_ = tag

            return prop

        # add properties to namespace
        for tag, (field_name, field_type) in enumerate(fields.items()):
            assert field_name not in ns
            ns[field_name] = _make_prop(field_type, tag)

        t = super().__new__(mcs, name, bases, ns, **kwargs)
        t._field_table_ = FrozenDict(fields)
        return t

    def __getitem__(cls, idx):
        if cls.is_bound:
            return super().__getitem__(idx)
        else:
            raise TypeError("Cannot bind TaggedUnion types with getitem")

    @property
    def field_dict(cls):
        return MappingProxyType(cls._field_table_)

    def enumerate(cls):
        for tag, field in cls.field_dict.items():
            if isinstance(field, BoundMeta):
                yield from map(lambda v: cls(**{tag: v}), field.enumerate())
            else:
                yield cls(**{tag: field()})


class EnumMeta(_AttrSyntax, BoundMeta):
    class Auto:
        def __repr__(self):
            return 'Auto()'

    FIELDS_T = int, Auto
    ORDERED = False

    @classmethod
    def _from_fields(mcs, fields, name, bases, ns, **kwargs):
        enum_base = None
        for base in bases:
            if isinstance(base, mcs):
                if enum_base is None:
                    enum_base = base
                else:
                    raise TypeError('Can only inherit from one enum type')

        cls = super().__new__(mcs, name, bases, ns, **kwargs)

        name_table = dict()
        for name, value in fields.items():
            elem = cls.__new__(cls)
            cls.__init__(elem, value)
            setattr(elem, '_name_', name)
            name_table[name] = elem
            setattr(cls, name, elem)

        cls._fields_ = tuple(name_table.values())
        cls._field_table_ = name_table

        if enum_base is not None:
            cls._unbound_base_ = enum_base

        return cls

    def __call__(cls, elem):
        if not isinstance(elem, cls):
            raise TypeError('Enums cannot be constructed by value')
        return elem

    @property
    def field_dict(cls):
        return MappingProxyType(cls._field_table_)

    def enumerate(cls):
        yield from cls.fields

    def rebind(cls, A: type, B: type, rebind_sub_types: bool = False, rebind_recursive: bool = True):
        # Enums aren't bound to types
        # could potentialy rebind values but that seems annoying
        return cls
