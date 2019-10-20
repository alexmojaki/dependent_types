from dependent_types.arrows import arrow
from dependent_types.core import Type, Instance
from dependent_types.utils import with_needed_parens


class PropInstance(Instance):
    def __and__(self, right):
        return AndInstance(self, right)

    def __or__(self, right):
        if isinstance(right, Prop):
            right = right(f"{with_needed_parens(right.name)}()")

        assert isinstance(right, PropInstance)
        return OrInstance(self, right)


class Prop(Type):
    type = Type
    instance_class = PropInstance

    def __and__(self, right):
        return And(self, right)

    def __or__(self, right):
        if isinstance(right, Prop):
            return Or(self, right)
        elif isinstance(right, PropInstance):
            left = self(f"{with_needed_parens(self.name)}()")
            return OrInstance(left, right)
        else:
            raise TypeError


class BinaryBooleanProp(Prop):
    symbol = None
    method = None

    def __init__(self, left, right):
        self.left = left
        self.right = right
        super().__init__(
            name=f"{with_needed_parens(left)} {self.symbol} {with_needed_parens(right)}",
            value=(self.__class__, left, right),
        )


class BinaryBooleanPropInstance(PropInstance):
    prop_class = None

    def __init__(self, left, right):
        self.left = left
        self.right = right
        super().__init__(
            typ=getattr(left.type, self.prop_class.method)(right.type),
            name=f"{with_needed_parens(left)} {self.prop_class.symbol} {with_needed_parens(right)}",
            value=(self.__class__, left, right),
        )


class And(BinaryBooleanProp):
    symbol = "&"
    method = "__and__"


class AndInstance(BinaryBooleanPropInstance):
    prop_class = And


class Or(BinaryBooleanProp):
    symbol = "|"
    method = "__or__"


class OrInstance(BinaryBooleanPropInstance):
    prop_class = Or

    def elim(self, from_left, from_right):
        left = arrow(from_left)(self.left)
        right = arrow(from_right)(self.right)
        if left.type != right.type:
            raise TypeError(f"Mismatched types {left.type} ({left.type.value}) and {right.type} ({right.type.value})")
        return PropInstance(
            typ=left.type,
            name=f"elim({left}, {right})",
            value=(self.__class__, left, right),
        )
