import types
import weakref
from .adt_meta import GetitemSyntax, AttrSyntax, EnumMeta


__ALL__ = ['new', 'make_modifier', 'is_modified', 'is_modifier', 'get_modifier', 'get_unmodified', 'strip_modifiers', 'push_modifiers']


_DEBUG = False
#special sentinal value
class _MISSING: pass

def new(klass, bind=_MISSING, *, name=_MISSING, module=_MISSING):
    class T(klass): pass
    if name is not _MISSING:
        T.__name__ = name
    if module is not _MISSING:
        T.__module__ = module

    if bind is not _MISSING:
        return T[bind]
    else:
        return T

class _ModifierMeta(type):
    _modifier_lookup = weakref.WeakKeyDictionary()
    def __instancecheck__(cls, obj):
        if cls is AbstractModifier:
            return super().__instancecheck__(obj)
        else:
            return type(obj) in cls._sub_classes

    def __subclasscheck__(cls, T):
        if cls is AbstractModifier:
            return super().__subclasscheck__(T)
        else:
            return T in cls._sub_classes

    def __call__(cls, *args):
        if cls is AbstractModifier:
            raise TypeError('Cannot instance or apply AbstractModifier')

        if len(args) != 1:
            return super().__call__(*args)

        unmod_cls = args[0]
        try:
            return cls._sub_class_cache[unmod_cls]
        except KeyError:
            pass

        mod_name = cls.__name__ + unmod_cls.__name__
        bases = [unmod_cls]
        for base in unmod_cls.__bases__:
            bases.append(cls(base))
        mod_cls = type(mod_name, tuple(bases), {})
        cls._register_modified(unmod_cls, mod_cls)
        return mod_cls

class AbstractModifier(metaclass=_ModifierMeta):
    def __init_subclass__(cls, **kwargs):
        cls._sub_class_cache = weakref.WeakValueDictionary()
        cls._sub_classes = weakref.WeakSet()

    @classmethod
    def _register_modified(cls, unmod_cls, mod_cls):
        type(cls)._modifier_lookup[mod_cls] = cls
        cls._sub_classes.add(mod_cls)
        cls._sub_class_cache[unmod_cls] = mod_cls
        if _DEBUG:
            # O(n) assert, but its a pretty key invariant
            assert set(cls._sub_classes) == set(cls._sub_class_cache.values())

def is_modified(T):
    return T in _ModifierMeta._modifier_lookup

def is_modifier(T):
    return issubclass(T, AbstractModifier)

def get_modifier(T):
    if is_modified(T):
        return _ModifierMeta._modifier_lookup[T]
    else:
        raise TypeError(f'{T} has no modifiers')

def get_unmodified(T):
    if is_modified(T):
        unmod = T.__bases__[0]
        if _DEBUG:
            # Not an expensive assert but as there is a
            # already a debug guard might as well use it.
            mod = get_modifier(T)
            assert mod._sub_class_cache[unmod] is T
        return unmod
    else:
        raise TypeError(f'{T} has no modifiers')

def get_all_modifiers(T):
    if is_modified(T):
        yield from get_all_modifiers(get_unmodified(T))
        yield get_modifier(T)

_mod_cache = weakref.WeakValueDictionary()
# This is a factory for type modifiers.
def make_modifier(name, cache=False):
    if cache:
        try:
            return _mod_cache[name]
        except KeyError:
            pass

    ModType = _ModifierMeta(name, (AbstractModifier, ), {})

    if cache:
        return _mod_cache.setdefault(name, ModType)

    return ModType

def unwrap_modifier(T):
    if not is_modified(T):
        return T, []
    mod = get_modifier(T)
    unmod = get_unmodified(T)
    unmod, mods = unwrap_modifier(unmod)
    mods.append(mod)
    return unmod, mods

def wrap_modifier(T, mods):
    wrapped = T
    if len(set(mods)) != len(mods):
        raise TypeError(f"{mods} must contain no duplicates")
    for mod in mods:
        wrapped = mod(wrapped)
    return wrapped

#Takes an ADT type and removes any modifiers on any level of the Tree
def strip_modifiers(adt_t):
    #remove modifiers from this level
    adt_t, _ = unwrap_modifier(adt_t)
    if isinstance(adt_t, AttrSyntax) and not isinstance(adt_t, EnumMeta):
        new_fields = {n:strip_modifiers(sub_adt_t) for n, sub_adt_t in adt_t.field_dict.items()}
        return adt_t.unbound_t.from_fields(adt_t.__name__, new_fields)
    elif isinstance(adt_t, GetitemSyntax):
        new_fields = [strip_modifiers(sub_adt_t) for sub_adt_t in adt_t.fields]
        return adt_t.unbound_t[new_fields]
    else:
        return adt_t

#Takes an ADT type and pushes all the modifiers from internal nodes to leaf nodes
def push_modifiers(adt_t, mods=[]):
    #remove modifiers from this level
    adt_t, new_mods = unwrap_modifier(adt_t)
    mods = new_mods + mods
    if isinstance(adt_t, AttrSyntax) and not isinstance(adt_t, EnumMeta):
        new_fields = {n:push_modifiers(sub_adt_t, mods) for n, sub_adt_t in adt_t.field_dict.items()}
        return adt_t.unbound_t.from_fields(adt_t.__name__, new_fields)
    elif isinstance(adt_t, GetitemSyntax):
        new_fields = [push_modifiers(sub_adt_t, mods) for sub_adt_t in adt_t.fields]
        return adt_t.unbound_t[new_fields]
    else:
        return wrap_modifier(adt_t, mods)


