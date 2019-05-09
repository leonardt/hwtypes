import itertools as it
import typing as tp

import weakref

from types import MappingProxyType
from collections.abc import Mapping, MutableMapping

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


def _is_descriptor(obj):
    return hasattr(obj, '__get__') or hasattr(obj, '__set__') or hasattr(obj, '__delete__')


class _key_map_dict(Mapping):
    def __init__(self, f: Mapping, d: Mapping):
        self._f = f
        self._d = d

    def __getitem__(self, key):
        return self._d[self._f[key]]

    def __iter__(self):
        yield from self._f

    def __len__(self):
        return len(self._f)

    def __repr__(self):
        c = []
        for k,v in self.items():
            c.append('{}:{}'.format(k,v))
        return f'{type(self).__name__}({",".join(c)})'


def is_adt_type(t):
    return isinstance(t, BoundMeta)


class BoundMeta(type):
    # (UnboundType, (types...)) : BoundType
    _class_cache = weakref.WeakValueDictionary()
    # BoundType : (types...)
    # UnboundType : None
    _class_info  = weakref.WeakKeyDictionary()

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

    def __new__(mcs, name, bases, namespace, **kwargs):
        bound_types = None
        for base in bases:
            if isinstance(base, BoundMeta) and base.is_bound:
                if bound_types is None:
                    bound_types = base.fields
                elif bound_types != base.fields:
                    raise TypeError("Can't inherit from multiple different bound_types")


        t = super().__new__(mcs, name, bases, namespace, **kwargs)
        if bound_types is not None:
            bound_types = t._fields_cb(bound_types)

        mcs._class_info[t] = bound_types

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
        t = type(cls)(class_name, bases, {})
        t.__module__ = cls.__module__
        BoundMeta._class_cache[cls, idx] = t
        BoundMeta._class_info[t] = idx
        return t

    @property
    def fields(cls):
        return BoundMeta._class_info[cls]

    @property
    def is_bound(cls) -> bool:
        return BoundMeta._class_info[cls] is not None

    def __repr__(cls):
        return f"{cls.__name__}"

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

class ProductMeta(TupleMeta):
    # ProductType : (FieldName : FieldType)
    _field_table = weakref.WeakKeyDictionary()

    def __new__(mcs, name, bases, namespace, **kwargs):
        fields = {}
        ns = {}
        for base in bases:
            if base.is_bound:
                for k,v in base.field_dict.items():
                    if k in fields:
                        raise TypeError(f'Conflicting defintions of field {k}')
                    else:
                        fields[k] = v
        for k, v in namespace.items():
            if isinstance(v, type):
                if k in fields:
                    raise TypeError(f'Conflicting defintions of field {k}')
                else:
                    fields[k] = v
            else:
                ns[k] = v

        if fields:
            return mcs.from_fields(fields, name, bases, ns,  **kwargs)
        else:
            return super().__new__(mcs, name, bases, ns, **kwargs)

    @classmethod
    def from_fields(mcs, fields, name, bases, ns, **kwargs):
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
        #this is all realy gross but I don't know how to do this cleanly

        #need to build t so I can call super()
        t = super().__new__(mcs, name, bases, ns, **kwargs)
        gs = {name : t, 'ProductMeta' : ProductMeta}
        ls = {}

        arg_list = ','.join(fields.keys())
        type_sig = ','.join(f'{k}: {v.__name__!r}' for k,v in fields.items())

        #build __new__
        __new__ = f'''
def __new__(cls, {type_sig}):
    return super({name}, cls).__new__(cls, {arg_list})
'''
        exec(__new__, gs, ls)
        t.__new__ = ls['__new__']

        #build __init__
        __init__ = f'''
def __init__(self, {type_sig}):
    return super({name}, self).__init__({arg_list})
'''
        exec(__init__, gs, ls)
        t.__init__ = ls['__init__']

        idx_table = dict((k, i) for i,k in enumerate(fields.keys()))

        #build properties
        for field_name in fields.keys():
            prop = f'''
@property
def {field_name}(self):
    return self[{idx_table[field_name]}]

@{field_name}.setter
def {field_name}(self, value):
    self[{idx_table[field_name]}] = value
'''
            exec(prop, gs, ls)
            setattr(t, field_name, ls[field_name])

        #Store the field indexs
        mcs._field_table[t] = _key_map_dict(idx_table, t)
        return t

    def __getattribute__(cls, name):
        try:
            return type(cls)._field_table[cls][name]
        except KeyError:
            pass
        return super().__getattribute__(name)

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
        return MappingProxyType(type(cls)._field_table[cls])


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
    # EnumType : (ElemName : Elem)
    _elem_name_table = weakref.WeakKeyDictionary()

    class Auto:
        def __repr__(self):
            return 'Auto()'

    def __new__(mcs, cls_name, bases, namespace, **kwargs):
        elems = {}
        ns = {}

        for k, v in namespace.items():
            if isinstance(v,  (int, mcs.Auto)):
                elems[k] = v
            elif _is_dunder(k) or _is_descriptor(v):
                ns[k] = v
            else:
                raise TypeError(f'Enum value should be int not {type(v)}')

        t = super().__new__(mcs, cls_name, bases, ns, **kwargs)

        if not elems:
            return t


        mcs._elem_name_table[t] = name_table = {}

        for name, value in elems.items():
            elem = t.__new__(t)
            elem.__init__(value)
            setattr(elem, '_name_', name)
            name_table[name] = elem

        super()._class_info[t] = tuple(name_table.values())

        return t

    def __call__(cls, elem):
        if not isinstance(elem, cls):
            raise TypeError('Enums cannot be constructed by value')
        return elem

    def __getattribute__(cls, name):
        try:
            return type(cls)._elem_name_table[cls][name]
        except KeyError:
            pass
        return super().__getattribute__(name)

    @property
    def field_dict(cls):
        return MappingProxyType(type(cls)._elem_name_table[cls])

    def enumerate(cls):
        yield from cls.fields
