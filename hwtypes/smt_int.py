import itertools as it
import functools as ft
from .smt_bit_vector import SMTBit, SMTBitVector

import pysmt
import pysmt.shortcuts as smt
from pysmt.typing import INT

from collections import defaultdict
import re
import warnings
import weakref

__ALL__ = ['SMTInt']

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

def int_cast(fn):
    @ft.wraps(fn)
    def wrapped(self, other):
        if isinstance(other, SMTInt):
            return fn(self, other)
        else:
            try:
                other = SMTInt(other)
            except TypeError:
                return NotImplemented
            return fn(self, other)
    return wrapped

class SMTInt:
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
            self._value = smt.Symbol(name, INT)
        elif isinstance(value, pysmt.fnode.FNode):
            if value.get_type().is_int_type():
                self._value = value
            elif value.get_type().is_bv_type():
                self._value = smt.BVToNatural(value)
            else:
                raise TypeError(f'Expected int type not {value.get_type()}')
        elif isinstance(value, SMTInt):
            self._value = value._value
        elif isinstance(value, SMTBitVector):
            self._value = smt.BVToNatural(value.value)
        elif isinstance(value, bool):
            self._value = smt.Int(int(value))
        elif isinstance(value, int):
            self._value = smt.Int(value)
        elif hasattr(value, '__int__'):
            self._value = smt.Int(int(value))
        else:
            raise TypeError("Can't coerce {} to Int".format(type(value)))

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

    def __neg__(self):
        return SMTInt(0) - self

    @int_cast
    def __sub__(self, other: 'SMTInt') -> 'SMTInt':
        return SMTInt(self.value - other.value)

    @int_cast
    def __add__(self, other: 'SMTInt') -> 'SMTInt':
        return SMTInt(self.value + other.value)

    @int_cast
    def __mul__(self, other: 'SMTInt') -> 'SMTInt':
        return SMTInt(self.value * other.value)

    @int_cast
    def __floordiv__(self, other: 'SMTInt') -> 'SMTInt':
        return SMTInt(smt.Div(self.value, other.value))

    @int_cast
    def __ge__(self, other: 'SMTInt') -> SMTBit:
        return SMTBit(self.value >= other.value)

    @int_cast
    def __gt__(self, other: 'SMTInt') -> SMTBit:
        return SMTBit(self.value > other.value)

    @int_cast
    def __le__(self, other: 'SMTInt') -> SMTBit:
        return SMTBit(self.value <= other.value)

    @int_cast
    def __lt__(self, other: 'SMTInt') -> SMTBit:
        return SMTBit(self.value < other.value)

    @int_cast
    def __eq__(self, other: 'SMTInt') -> SMTBit:
        return SMTBit(smt.Equals(self.value, other.value))

    @int_cast
    def __ne__(self, other: 'SMTInt') -> SMTBit:
        return SMTBit(smt.NotEquals(self.value, other.value))
