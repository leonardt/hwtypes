import types
import weakref

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
    def __instancecheck__(cls, obj):
        return type(obj) in cls._sub_classes.values()

    def __subclasscheck__(cls, typ):
        return typ in cls._sub_classes.values()

    def __call__(cls, *args):
        if len(args) != 1:
            return super().__call__(*args)
        sub = args[0]
        try:
            return cls._sub_classes[sub]
        except KeyError:
            pass

        mod_sub_name = cls.__name__ + sub.__name__
        mod_sub = type(mod_sub_name, (sub,), {})
        return cls._sub_classes.setdefault(sub, mod_sub)

_mod_cache = weakref.WeakValueDictionary()
# This is a factory for type modifiers.
def make_modifier(name, cache=False):
    if cache:
        try:
            return _mod_cache[name]
        except KeyError:
            pass

    ModType = _ModifierMeta(name, (), {'_sub_classes' : weakref.WeakValueDictionary()})

    if cache:
        return _mod_cache.setdefault(name, ModType)

    return ModType
