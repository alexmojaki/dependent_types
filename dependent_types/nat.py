from . import core
from . import arrows


class NatInstance(core.Instance):
    @staticmethod
    def from_number(n: int):
        assert isinstance(n, int)
        assert n >= 0
        if n == 0:
            return ZERO
        else:
            result = ZERO
            for _ in range(n):
                result = successor(result)
            return result

    @staticmethod
    def ensure_nat_instance(other):
        if isinstance(other, NatInstance):
            return other
        elif isinstance(other, int):
            return NatInstance.from_number(other)
        else:
            raise TypeError(f"{other} cannot be cast to Natural number")

    @property
    def predecessor(self):
        if self.value:
            _, arr, args, kwargs = self.value
            if arr == successor:
                (self_predecessor,) = args
                return self_predecessor

        return None
            


    def __add__(self, other):
        other = NatInstance.ensure_nat_instance(other)

        if self == ZERO:
            return other
        elif other == ZERO:
            return self
        else:
            if self.predecessor:
                return successor(self.predecessor + other)

            if other.predecessor:
                return successor(self+ other.predecessor)

            return add(self, other)
                
        raise TypeError(f"Cannot resolve {self} + {other}")


    def __mul__(self, other):
        other = NatInstance.ensure_nat_instance(other)

        if self == ZERO:
            return ZERO
        else:
            if self.predecessor:
                return (self.predecessor * other) + other
            if other.predecessor:
                return (self * other.predecessor) + self

            return mul(self, other)

        raise TypeError(f"Cannot resolve {self} * {other}")

    def __le__(self, other):
        if self == ZERO or self == other:
            return True
        elif other.predecessor:
            return self <= other.predecessor
        else:
            return False # TODO return a PROPOSITION "self <= other" !!            
        
        raise TypeError(f"Cannot resolve {self} <= {other}")




class NatType(core.Type):
    instance_class = NatInstance


Nat = NatType("Nat")
ZERO = Nat("0", value=0)


@arrows.arrow
def successor(n: Nat) -> Nat:
    ...

@arrows.arrow
def add(n: Nat, m:Nat) -> Nat:
    ...

@arrows.arrow
def mul(n: Nat, m:Nat) -> Nat:
    ...
