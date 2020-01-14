import functools as ft
import itertools as it
from .bit_vector_abc import InconsistentSizeError

def get_branch_type(branch):
    if isinstance(branch, tuple):
        return tuple(map(get_branch_type, branch))
    else:
        return type(branch)

def determine_return_type(bit_t, bv_t, t_branch, f_branch):
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
        elif isinstance(t_branch, bit_t) and isinstance(f_branch, bit_t):
            if issubclass(tb_t, fb_t):
                return fb_t
            elif issubclass(fb_t, tb_t):
                return tb_t
            else:
                raise TypeError(f'Branches have inconsistent types: {tb_t} and {fb_t}')
        elif isinstance(t_branch, bv_t) and isinstance(f_branch, bv_t):
            if tb_t.size != fb_t.size:
                raise InconsistentSizeError('Both branches must have the same size')
            elif issubclass(tb_t, fb_t):
                return fb_t
            elif issubclass(fb_t, tb_t):
                return tb_t
            else:
                raise TypeError(f'Branches have inconsistent types: {tb_t} and {fb_t}')
        elif isinstance(t_branch, bit_t):
            return tb_t
        elif isinstance(f_branch, bit_t):
            return fb_t
        elif isinstance(t_branch, bv_t):
            return tb_t
        elif isinstance(f_branch, bv_t):
            return fb_t
        else:
            raise TypeError(f'Cannot infer return type. '
                            f'Atleast one branch must be a {bv_t}, {bit_t}, or tuples')
    return _recurse(t_branch, f_branch)

def coerce_branch(r_type, branch):
    if isinstance(r_type, tuple):
        assert isinstance(branch, tuple)
        assert len(r_type) == len(branch)
        return tuple(coerce_branch(t, arg) for t, arg in zip(r_type, branch))
    else:
        return r_type(branch)

def push_ite(ite, t_branch, f_branch):
    def _recurse(t_branch, f_branch):
        if isinstance(t_branch, tuple):
            assert isinstance(f_branch, tuple)
            assert len(t_branch) == len(f_branch)
            return tuple(it.starmap(
                            _recurse,
                            zip(t_branch, f_branch)
                        ))
        else:
            return ite(t_branch, f_branch)
    return _recurse(t_branch, f_branch)

def build_ite(ite, bit_t, t_branch, f_branch,
              push_ite_to_leaves=False,
              cast_return=False):
    bv_t = bit_t.get_family().BitVector
    r_type = determine_return_type(bit_t, bv_t, t_branch, f_branch)
    t_branch = coerce_branch(r_type, t_branch)
    f_branch = coerce_branch(r_type, f_branch)

    if push_ite_to_leaves:
        r_val = push_ite(ite, t_branch, f_branch)
    else:
        r_val = ite(t_branch, f_branch)

    if cast_return:
        r_val = coerce_branch(r_type, r_val)

    return r_val
