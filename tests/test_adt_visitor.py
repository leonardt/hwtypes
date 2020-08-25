from hwtypes.adt import Tuple, Product, Enum, TaggedUnion, Sum
from hwtypes.adt_util import ADTVisitor, ADTInstVisitor


class FlattenT(ADTVisitor):
    def __init__(self):
        self.leaves = []

    def visit_leaf(self, n):
        self.leaves.append(n)

    def visit_Enum(self, n):
        self.leaves.append(n)


class FlattenI(ADTInstVisitor):
    def __init__(self):
        self.leaves = []

    def visit_leaf(self, n):
        self.leaves.append(n)

    def visit_Enum(self, n):
        self.leaves.append(n._value_)


class T1: pass
class T2: pass
class T3: pass
class T4: pass
class T5: pass

class Root(Product):
    leaf = T1

    class Branch(TaggedUnion):
        s_child = Sum[T2, T3]
        t_child = Tuple[T4, T5]

    class Tag(Enum):
        tag_a = Enum.Auto()
        tag_i = 1


def test_visit():
    flattener = FlattenT()
    flattener.visit(Root)

    assert set(flattener.leaves) == {T1, T2, T3, T4, T5, Root.Tag}

def test_visit_i():
    t1 = T1()
    t2 = T2()
    t3 = T3()
    t4 = T4()
    t5 = T5()

    root = Root(
            leaf=t1,
            Branch=Root.Branch(s_child=Sum[T2, T3](t3)),
            Tag=Root.Tag.tag_i
            )

    flattener = FlattenI()
    flattener.visit(root)

    assert set(flattener.leaves) == {t1, t3, 1}

