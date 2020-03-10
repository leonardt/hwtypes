import functools as ft
import itertools as it
import inspect
import types

from .bit_vector_abc import InconsistentSizeError
from .bit_vector_abc import BitVectorMeta, AbstractBitVector, AbstractBit

def _get_common_bases(t, s):
    if issubclass(t, s):
        return (s,)
    elif issubclass(s, t):
        return (t,)
    else:
        bases = set()
        for t_ in t.__bases__:
            bases.update(_get_common_bases(t_, s))

        for s_ in s.__bases__:
            bases.update(_get_common_bases(t, s_))

        # Filter to most specific types
        bases_ = set()
        for bi in bases:
            if not any(issubclass(bj, bi) for bj in bases if bi is not bj):
                bases_.add(bi)

        return tuple(bases_)

# used as a tag
class PolyBase: pass

class PolyType(type):
    _type_cache = {}
    def __getitem__(cls, args):
        T0, T1 = args
        try:
            return cls._type_cache[args]
        except KeyError:
            pass

        if not cls._type_check(T0, T1):
            raise TypeError(f'Cannot construct {cls} from {T0} and {T1}')
        if T0.get_family() is not T1.get_family():
            raise TypeError('Cannot construct PolyTypes across families')

        bases = *_get_common_bases(T0, T1), PolyBase
        class_name = f'{cls.__name__}[{T0.__name__}, {T1.__name__}]'
        meta, namespace, _ = types.prepare_class(class_name, bases)

        d0 = dict(inspect.getmembers(T0))
        d1 = dict(inspect.getmembers(T1))

        attrs = d0.keys() & d1.keys()
        for k in attrs:
            if k in {'_info_', '__int__', '__repr__', '__str__'}:
                continue

            m0 = inspect.getattr_static(T0, k)
            m1 = inspect.getattr_static(T1, k)
            namespace[k] = build_VCall([m0, m1])

        new_cls = meta(class_name, bases, namespace)

        genv = {'base': new_cls}
        lenv = {}

        # build __init__
        __init__ = f'''
def __init__(self, *args, _poly_select_, **kwargs):
    self._poly_select_ = _poly_select_
    return super(base, self).__init__(*args, **kwargs)
'''
        exec(__init__, genv, lenv)
        new_cls.__init__ = lenv['__init__']

        return cls._type_cache.setdefault(args, new_cls)

class PolyVector(metaclass=PolyType):
    @classmethod
    def _type_check(cls, T0, T1):
        if (issubclass(T0, AbstractBitVector)
            and issubclass(T1, AbstractBitVector)):
            if T0.size != T1.size:
                raise InconsistentSizeError(f'Cannot construct {cls} from {T0} and {T1}')
            else:
                return True
        else:
            return False

class PolyBit(metaclass=PolyType):
    @classmethod
    def _type_check(cls, T0, T1):
        return (issubclass(T0, AbstractBit)
                and issubclass(T1, AbstractBit))

def build_VCall(methods):
    if methods[0] is methods[1]:
        return methods[0]
    else:
        def VCall(self, *args, **kwargs):
            v0 = methods[0](self, *args, **kwargs)
            v1 = methods[1](self, *args, **kwargs)
            if v0 is NotImplemented or v0 is NotImplemented:
                return NotImplemented
            return select.ite(v0, v1)
        return VCall


def get_branch_type(branch):
    if isinstance(branch, tuple):
        return tuple(map(get_branch_type, branch))
    else:
        return type(branch)

def determine_return_type(t_branch, f_branch):
    def _recurse(t_branch, f_branch):
        tb_t = get_branch_type(t_branch)
        fb_t = get_branch_type(f_branch)

        if (isinstance(tb_t, tuple)
            and isinstance(fb_t, tuple)
            and len(tb_t) == len(fb_t)):
            try:
                return tuple(
                    it.starmap(
                        _recurse,
                        zip(t_branch, f_branch)
                    )
                )
            except (TypeError, InconsistentSizeError):
                raise TypeError(f'Branches have inconsistent types: '
                                f'{tb_t} and {fb_t}') from None
        elif (isinstance(tb_t, tuple)
              or isinstance(fb_t, tuple)):
            raise TypeError(f'Branches have inconsistent types: {tb_t} and {fb_t}')
        elif issubclass(tb_t, AbstractBit) and issubclass(fb_t, AbstractBit):
            if tb_t is fb_t:
                return tb_t
            return PolyBit[tb_t, fb_t]
        elif issubclass(tb_t, AbstractBitVector) and issubclass(fb_t, AbstractBitVector):
            if tb_t is fb_t:
                return tb_t
            return PolyVector[tb_t, fb_t]
        else:
            raise TypeError(f'tb_t: {tb_t}, fb_t: {fb_t}')

    return _recurse(t_branch, f_branch)

def coerce_branch(r_type, select, branch):
    if isinstance(r_type, tuple):
        assert isinstance(branch, tuple)
        assert len(r_type) == len(branch)
        return tuple(coerce_branch(t, select, arg) for t, arg in zip(r_type, branch))
    elif issubclass(r_type, PolyBase):
        return r_type(branch, _poly_select_ = select)
    else:
        return r_type(branch)

def push_ite(ite, select, t_branch, f_branch):
    def _recurse(t_branch, f_branch):
        if isinstance(t_branch, tuple):
            assert isinstance(f_branch, tuple)
            assert len(t_branch) == len(f_branch)
            return tuple(it.starmap(
                            _recurse,
                            zip(t_branch, f_branch)
                        ))
        else:
            return ite(select, t_branch, f_branch)
    return _recurse(t_branch, f_branch)

def build_ite(ite, select, t_branch, f_branch):
    r_type = determine_return_type(t_branch, f_branch)
    r_val = push_ite(ite, select, t_branch, f_branch)
    r_val = coerce_branch(r_type, select, r_val)
    return r_val
