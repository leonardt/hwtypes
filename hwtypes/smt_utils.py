from . import SMTBit
import operator
from functools import partial, reduce
import abc

_or_reduce = partial(reduce, operator.or_)
_and_reduce = partial(reduce, operator.and_)

class FormulaConstructor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def serialize(self, line_prefix, indent):
        ...

    @abc.abstractmethod
    def to_hwtypes(self):
        ...

def _to_hwtypes(v):
    if isinstance(v, FormulaConstructor):
        return v.to_hwtypes()
    return v

def _value_to_str(v, line_prefix, indent):
    if isinstance(v, FormulaConstructor):
        return v.serialize(line_prefix, indent)
    else:
        return f"{line_prefix}{v.value.serialize()}"

def _op_to_str(vs, opname, line_prefix, indent):
    new_line_prefix = line_prefix + indent
    return "\n".join([
        f"{line_prefix}{opname}(",
        ",\n".join([_value_to_str(v, new_line_prefix, indent) for v in vs]),
        f"{line_prefix})"
    ])
def _check(vs):
    if not all(isinstance(v, (FormulaConstructor, SMTBit)) for v in vs):
        raise ValueError("Formula Constructor requires SMTBit or other FormulaConstructors")

class And(FormulaConstructor):
    def __init__(self, values: list):
        _check(values)
        self.values = list(values)

    def serialize(self, line_prefix="", indent="|   "):
        return _op_to_str(self.values, "And", line_prefix, indent)

    def to_hwtypes(self):
        if len(self.values) == 0:
            return SMTBit(True)
        return _and_reduce(_to_hwtypes(v) for v in self.values)

class Or(FormulaConstructor):
    def __init__(self, values: list):
        _check(values)
        self.values = list(values)

    def serialize(self, line_prefix="", indent="|   "):
        return _op_to_str(self.values, "Or", line_prefix, indent)

    def to_hwtypes(self):
        if len(self.values)==0:
            return SMTBit(False)
        return _or_reduce(_to_hwtypes(v) for v in self.values)

class Implies(FormulaConstructor):
    def __init__(self, p, q):
        _check([p, q])
        self.p = p
        self.q = q

    def serialize(self, line_prefix="", indent="|   "):
        return _op_to_str((self.p, self.q), "Implies", line_prefix, indent)

    def to_hwtypes(self):
        return (~_to_hwtypes(self.p)) | _to_hwtypes(self.q)
