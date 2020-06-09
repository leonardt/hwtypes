import typing as tp
import itertools as it
import functools as ft
from .bit_vector_abc import AbstractBitVector, AbstractBit, TypeFamily, InconsistentSizeError
from .bit_vector_util import build_ite

from abc import abstractmethod

import pysmt
import pysmt.shortcuts as smt
from pysmt.typing import  BVType, BOOL


from collections import defaultdict
import re
import warnings
import weakref

import random

__ALL__ = ['SMTBitVector', 'SMTNumVector', 'SMTSIntVector', 'SMTUIntVector']

_var_counters = defaultdict(it.count)
_name_table = weakref.WeakValueDictionary()

def _gen_name(prefix='V'):
    name = f'{prefix}_{next(_var_counters[prefix])}'
    while name in _name_table:
        name = f'{prefix}_{next(_var_counters[prefix])}'
    return name

_name_re = re.compile(r'V_\d+')

class _SMYBOLIC:
    def __repr__(self):
        return 'SYMBOLIC'

class _AUTOMATIC:
    def __repr__(self):
        return 'AUTOMATIC'

SMYBOLIC = _SMYBOLIC()
AUTOMATIC = _AUTOMATIC()

def bit_cast(fn):
    @ft.wraps(fn)
    def wrapped(self, other):
        if isinstance(other, SMTBit):
            return fn(self, other)
        else:
            try:
                other = SMTBit(other)
            except TypeError:
                return NotImplemented
            return fn(self, other)
    return wrapped

class SMTBit(AbstractBit):
    @staticmethod
    def get_family() -> TypeFamily:
        return _Family_

    def __init__(self, value=SMYBOLIC, *, name=AUTOMATIC, prefix=AUTOMATIC):
        if (name is not AUTOMATIC or prefix is not AUTOMATIC) and value is not SMYBOLIC:
            raise TypeError('Can only name symbolic variables')
        elif name is not AUTOMATIC and prefix is not AUTOMATIC:
            raise ValueError('Can only set either name or prefix not both')
        elif name is not AUTOMATIC:
            if not isinstance(name, str):
                raise TypeError('Name must be string')
            elif name in _name_table:
                raise ValueError(f'Name {name} already in use')
            elif _name_re.fullmatch(name):
                warnings.warn('Name looks like an auto generated name, this might break things')
            _name_table[name] = self
        elif prefix is not AUTOMATIC:
            name = _gen_name(prefix)
            _name_table[name] = self
        elif name is AUTOMATIC and value is SMYBOLIC:
            name = _gen_name()
            _name_table[name] = self

        if value is SMYBOLIC:
            self._value = smt.Symbol(name, BOOL)
        elif isinstance(value, pysmt.fnode.FNode):
            if value.get_type().is_bool_type():
                self._value = value
            else:
                raise TypeError(f'Expected bool type not {value.get_type()}')
        elif isinstance(value, SMTBit):
            if name is not AUTOMATIC and name != value.name:
                warnings.warn('Changing the name of a SMTBit does not cause a new underlying smt variable to be created')
            self._value = value._value
        elif isinstance(value, bool):
            self._value = smt.Bool(value)
        elif isinstance(value, int):
            if value not in {0, 1}:
                raise ValueError('Bit must have value 0 or 1 not {}'.format(value))
            self._value = smt.Bool(bool(value))
        elif hasattr(value, '__bool__'):
            self._value = smt.Bool(bool(value))
        else:
            raise TypeError("Can't coerce {} to Bit".format(type(value)))

        self._name = name
        self._value = smt.simplify(self._value)

    def __repr__(self):
        if self._name is not AUTOMATIC:
            return f'{type(self)}({self._name})'
        else:
            return f'{type(self)}({self._value})'

    @property
    def value(self):
        return self._value

    @bit_cast
    def __eq__(self, other : 'SMTBit') -> 'SMTBit':
        return type(self)(smt.Iff(self.value, other.value))

    @bit_cast
    def __ne__(self, other : 'SMTBit') -> 'SMTBit':
        return type(self)(smt.Not(smt.Iff(self.value, other.value)))

    def __invert__(self) -> 'SMTBit':
        return type(self)(smt.Not(self.value))

    @bit_cast
    def __and__(self, other : 'SMTBit') -> 'SMTBit':
        return type(self)(smt.And(self.value, other.value))

    @bit_cast
    def __or__(self, other : 'SMTBit') -> 'SMTBit':
        return type(self)(smt.Or(self.value, other.value))

    @bit_cast
    def __xor__(self, other : 'SMTBit') -> 'SMTBit':
        return type(self)(smt.Xor(self.value, other.value))

    def ite(self, t_branch, f_branch):
        def _ite(select, t_branch, f_branch):
            return smt.Ite(select.value, t_branch.value, f_branch.value)


        return build_ite(_ite, self, t_branch, f_branch)

    def substitute(self, *subs : tp.List[tp.Tuple['SMTBit', 'SMTBit']]):
        return SMTBit(
            self.value.substitute(
                {from_.value:to.value for from_, to in subs}
            )
        )


def _coerce(T : tp.Type['SMTBitVector'], val : tp.Any) -> 'SMTBitVector':
    if not isinstance(val, SMTBitVector):
        return T(val)
    elif val.size != T.size:
        raise InconsistentSizeError('Inconsistent size')
    else:
        return val

def bv_cast(fn : tp.Callable[['SMTBitVector', 'SMTBitVector'], tp.Any]) -> tp.Callable[['SMTBitVector', tp.Any], tp.Any]:
    @ft.wraps(fn)
    def wrapped(self : 'SMTBitVector', other : tp.Any) -> tp.Any:
        other = _coerce(type(self), other)
        return fn(self, other)
    return wrapped

def int_cast(fn : tp.Callable[['SMTBitVector', int], tp.Any]) -> tp.Callable[['SMTBitVector', tp.Any], tp.Any]:
    @ft.wraps(fn)
    def wrapped(self :  'SMTBitVector', other :  tp.Any) -> tp.Any:
        other = int(other)
        return fn(self, other)
    return wrapped

class SMTBitVector(AbstractBitVector):
    @staticmethod
    def get_family() -> TypeFamily:
        return _Family_

    def __init__(self, value=SMYBOLIC, *, name=AUTOMATIC, prefix=AUTOMATIC):
        if (name is not AUTOMATIC or prefix is not AUTOMATIC) and value is not SMYBOLIC:
            raise TypeError('Can only name symbolic variables')
        elif name is not AUTOMATIC and prefix is not AUTOMATIC:
            raise ValueError('Can only set either name or prefix not both')
        elif name is not AUTOMATIC:
            if not isinstance(name, str):
                raise TypeError('Name must be string')
            elif name in _name_table:
                raise ValueError(f'Name {name} already in use')
            elif _name_re.fullmatch(name):
                warnings.warn('Name looks like an auto generated name, this might break things')
            _name_table[name] = self
        elif prefix is not AUTOMATIC:
            name = _gen_name(prefix)
            _name_table[name] = self
        elif name is AUTOMATIC and value is SMYBOLIC:
            name = _gen_name()
            _name_table[name] = self

        self._name = name

        T = BVType(self.size)

        if value is SMYBOLIC:
            self._value = smt.Symbol(name, T)
        elif isinstance(value, pysmt.fnode.FNode):
            t = value.get_type()
            if t is T:
                self._value = value
            else:
                raise TypeError(f'Expected {T} not {t}')
        elif isinstance(value, SMTBitVector):
            if name is not AUTOMATIC and name != value.name:
                warnings.warn('Changing the name of a SMTBitVector does not cause a new underlying smt variable to be created')

            ext = self.size - value.size

            if ext < 0:
                warnings.warn('Truncating value from {} to {}'.format(type(value), type(self)))
                self._value = value[:self.size].value
            elif ext > 0:
                self._value = value.zext(ext).value
            else:
                self._value = value.value

        elif isinstance(value, SMTBit):
            self._value = smt.Ite(value.value, smt.BVOne(self.size), smt.BVZero(self.size))

        elif isinstance(value, tp.Sequence):
            if len(value) != self.size:
                raise ValueError('Iterable is not the correct size')
            cls = type(self)
            B1 = cls.unsized_t[1]
            self._value = ft.reduce(lambda acc, elem : acc.concat(elem), map(B1, value)).value
        elif isinstance(value, int):
            self._value =  smt.BV(value % (1 << self.size), self.size)

        elif hasattr(value, '__int__'):
            value = int(value)
            self._value = smt.BV(value, self.size)
        else:
            raise TypeError("Can't coerce {} to SMTBitVector".format(type(value)))

        self._value = smt.simplify(self._value)
        assert self._value.get_type() is T

    def make_constant(self, value, size:tp.Optional[int]=None):
        if size is None:
            size = self.size
        return type(self).unsized_t[size](value)

    @property
    def value(self):
        return self._value

    @property
    def num_bits(self):
        return self.size

    def __repr__(self):
        if self._name is not AUTOMATIC:
            return f'{type(self)}({self._name})'
        else:
            return f'{type(self)}({self._value})'

    def __getitem__(self, index):
        size = self.size
        if isinstance(index, slice):
            start, stop, step = index.start, index.stop, index.step

            if start is None:
                start = 0
            elif start < 0:
                start = size + start

            if stop is None:
                stop = size
            elif stop < 0:
                stop = size + stop

            stop = min(stop, size)

            if step is None:
                step = 1
            elif step != 1:
                raise IndexError('SMT extract does not support step != 1')

            v = self.value[start:stop-1]
            return type(self).unsized_t[v.get_type().width](v)
        elif isinstance(index, int):
            if index < 0:
                index = size+index

            if not (0 <= index < size):
                raise IndexError()

            v = self.value[index]
            return self.get_family().Bit(smt.Equals(v, smt.BV(1, 1)))
        else:
            raise TypeError()


    def __setitem__(self, index, value):
        if isinstance(index, slice):
            raise NotImplementedError()
        else:
            if not (isinstance(value, bool) or isinstance(value, SMTBit) or (isinstance(value, int) and value in {0, 1})):
                raise ValueError("Second argument __setitem__ on a single BitVector index should be a bit, boolean or 0 or 1, not {value}".format(value=value))

            if index < 0:
                index = self.size+index

            if not (0 <= index < self.size):
                raise IndexError()

            mask = type(self)(1 << index)
            self._value = SMTBit(value).ite(self | mask,  self & ~mask)._value


    def __len__(self):
        return self.size

    def concat(self, other):
        T = type(self).unsized_t
        if not isinstance(other, T):
            raise TypeError(f'value must of type {T} not {type(other)}')
        return T[self.size + other.size](smt.BVConcat(other.value, self.value))

    def bvnot(self):
        return type(self)(smt.BVNot(self.value))

    @bv_cast
    def bvand(self, other):
        return type(self)(smt.BVAnd(self.value, other.value))

    @bv_cast
    def bvnand(self, other):
        return type(self)(smt.BVNot(smt.BVAnd(self.value, other.value)))

    @bv_cast
    def bvor(self, other):
        return type(self)(smt.BVOr(self.value, other.value))

    @bv_cast
    def bvnor(self, other):
        return type(self)(smt.BVNot(smt.BVOr(self.value, other.value)))

    @bv_cast
    def bvxor(self, other):
        return type(self)(smt.BVXor(self.value, other.value))

    @bv_cast
    def bvxnor(self, other):
        return type(self)(smt.BVNot(smt.BVXor(self.value, other.value)))

    @bv_cast
    def bvshl(self, other):
        return type(self)(smt.BVLShl(self.value, other.value))

    @bv_cast
    def bvlshr(self, other):
        return type(self)(smt.BVLShr(self.value, other.value))

    @bv_cast
    def bvashr(self, other):
        return type(self)(smt.BVAShr(self.value, other.value))

    @int_cast
    def bvrol(self, other):
        return type(self)(smt.get_env().formula_manager.BVRol(self.value, other))

    @int_cast
    def bvror(self, other):
        return type(self)(smt.get_env().formula_manager.BVRor(self.value, other))

    @bv_cast
    def bvcomp(self, other):
        return type(self).unsized_t[1](smt.BVComp(self.value, other.value))

    @bv_cast
    def bveq(self,  other):
        return self.get_family().Bit(smt.Equals(self.value, other.value))

    @bv_cast
    def bvne(self, other):
        return self.get_family().Bit(smt.NotEquals(self.value, other.value))

    @bv_cast
    def bvult(self, other):
        return self.get_family().Bit(smt.BVULT(self.value, other.value))

    @bv_cast
    def bvule(self, other):
        return self.get_family().Bit(smt.BVULE(self.value, other.value))

    @bv_cast
    def bvugt(self, other):
        return self.get_family().Bit(smt.BVUGT(self.value, other.value))

    @bv_cast
    def bvuge(self, other):
        return self.get_family().Bit(smt.BVUGE(self.value, other.value))

    @bv_cast
    def bvslt(self, other):
        return self.get_family().Bit(smt.BVSLT(self.value, other.value))

    @bv_cast
    def bvsle(self, other):
        return self.get_family().Bit(smt.BVSLE(self.value, other.value))

    @bv_cast
    def bvsgt(self, other):
        return self.get_family().Bit(smt.BVSGT(self.value, other.value))

    @bv_cast
    def bvsge(self, other):
        return self.get_family().Bit(smt.BVSGE(self.value, other.value))

    def bvneg(self):
        return type(self)(smt.BVNeg(self.value))

    def adc(self, other : 'SMTBitVector', carry : SMTBit) -> tp.Tuple['BitVector', SMTBit]:
        """
        add with carry

        returns a two element tuple of the form (result, carry)

        """
        T = type(self)
        other = _coerce(T, other)
        carry = _coerce(T.unsized_t[1], carry)

        a = self.zext(1)
        b = other.zext(1)
        c = carry.zext(T.size)

        res = a + b + c
        return res[0:-1], res[-1]

    def ite(self, t_branch, f_branch):
        return self.bvne(0).ite(t_branch, f_branch)

    @bv_cast
    def bvadd(self, other):
        return type(self)(smt.BVAdd(self.value, other.value))

    @bv_cast
    def bvsub(self, other):
        return type(self)(smt.BVSub(self.value, other.value))

    @bv_cast
    def bvmul(self, other):
        return type(self)(smt.BVMul(self.value, other.value))

    @bv_cast
    def bvudiv(self, other):
        return type(self)(smt.BVUDiv(self.value, other.value))

    @bv_cast
    def bvurem(self, other):
        return type(self)(smt.BVURem(self.value, other.value))

    @bv_cast
    def bvsdiv(self, other):
        return type(self)(smt.BVSDiv(self.value, other.value))

    @bv_cast
    def bvsrem(self, other):
        return type(self)(smt.BVSRem(self.value, other.value))

    def __invert__(self): return self.bvnot()

    def __and__(self, other):
        try:
            return self.bvand(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __or__(self, other):
        try:
            return self.bvor(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __xor__(self, other):
        try:
            return self.bvxor(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented


    def __lshift__(self, other):
        try:
            return self.bvshl(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __rshift__(self, other):
        try:
            return self.bvlshr(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __neg__(self): return self.bvneg()

    def __add__(self, other):
        try:
            return self.bvadd(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __sub__(self, other):
        try:
            return self.bvsub(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __mul__(self, other):
        try:
            return self.bvmul(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __floordiv__(self, other):
        try:
            return self.bvudiv(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __mod__(self, other):
        try:
            return self.bvurem(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented


    def __eq__(self, other):
        try:
            return self.bveq(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __ne__(self, other):
        try:
            return self.bvne(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __ge__(self, other):
        try:
            return self.bvuge(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __gt__(self, other):
        try:
            return self.bvugt(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __le__(self, other):
        try:
            return self.bvule(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __lt__(self, other):
        try:
            return self.bvult(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError as e:
            return NotImplemented


    @int_cast
    def repeat(self, other):
        return type(self)(smt.get_env().formula_manager.BVRepeat(self.value, other))

    @int_cast
    def sext(self, ext):
        if ext < 0:
            raise ValueError()
        return type(self).unsized_t[self.size + ext](smt.BVSExt(self.value, ext))

    def ext(self, ext):
        return self.zext(ext)

    @int_cast
    def zext(self, ext):
        if ext < 0:
            raise ValueError()
        return type(self).unsized_t[self.size + ext](smt.BVZExt(self.value, ext))

    def substitute(self, *subs : tp.List[tp.Tuple["SBV", "SBV"]]):
        return SMTBitVector[self.size](
            self.value.substitute(
                {from_.value:to.value for from_, to in subs}
            )
        )


#    def bits(self):
#        return [(self >> i) & 1 for i in range(self.size)]
#
#    def __int__(self):
#        return self.as_uint()
#
#    def as_uint(self):
#        return self._value.bv_unsigned_value()
#
#    def as_sint(self):
#        return self._value.bv_signed_value()
#
#    @classmethod
#    def random(cls, width):
#        return cls.unsized_t[width](random.randint(0, (1 << width) - 1))

class SMTNumVector(SMTBitVector):
    pass

class SMTUIntVector(SMTNumVector):
    pass

class SMTSIntVector(SMTNumVector):
    def __rshift__(self, other):
        try:
            return self.bvashr(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __floordiv__(self, other):
        try:
            return self.bvsdiv(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __mod__(self, other):
        try:
            return self.bvsrem(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __ge__(self, other):
        try:
            return self.bvsge(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __gt__(self, other):
        try:
            return self.bvsgt(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def __lt__(self, other):
        try:
            return self.bvslt(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError as e:
            return NotImplemented

    def __le__(self, other):
        try:
            return self.bvsle(other)
        except InconsistentSizeError as e:
            raise e from None
        except TypeError:
            return NotImplemented

    def ext(self, other):
        return self.sext(other)



_Family_ = TypeFamily(SMTBit, SMTBitVector, SMTUIntVector, SMTSIntVector)
