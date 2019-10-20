from dependent_types import Type, Instance, arrow
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


def main():
    assert Prop.type is Type
    assert str(Prop) == "Prop"

    p = Prop("p")
    assert p.type is Prop
    assert str(p) == "p"

    q = Prop("q")
    a = p & q
    assert str(a) == "p & q"
    assert a.value == (And, p, q)

    hp = p("hp")
    hq = q("hq")
    assert hp.type is p
    assert str(hp) == "hp"

    ah = hp & hq
    assert ah.type == p & q
    assert str(ah) == "hp & hq"
    assert ah.value == (AndInstance, hp, hq)

    assert (hp | hq).type == p | q

    @arrow
    def and_comm(h: p & q) -> q & p:
        return h.right & h.left

    assert and_comm(hp & hq) == hq & hp

    assert (hp | q).type == (p | q)
    assert (p | hq).type == (p | q)
    assert str(hp | q) == "hp | q()"
    assert str(p | hq) == "p() | hq"

    test_or_assoc()


def test_or_assoc():
    """
    example : (p ∨ q) ∨ r -> p ∨ (q ∨ r) :=
        assume h: (p ∨ q) ∨ r,
        or.elim h
            (assume hleft : p ∨ q,
            or.elim hleft
                (assume hp: p, or.intro_left (q ∨ r) hp)
                (assume hq: q, or.intro_right p (or.intro_left r hq)))

            (assume hr: r, or.intro_right p (or.intro_right q hr))
    """
    p = Prop("p")
    q = Prop("q")
    r = Prop("r")

    goal = p | (q | r)

    @arrow
    def or_assoc(h: (p | q) | r) -> goal:
        def if_p_or_q(hleft: p | q) -> goal:
            def if_p(hp: p) -> goal:
                return hp | (q | r)

            def if_q(hq: q) -> goal:
                return p | (hq | r)

            return hleft.elim(if_p, if_q)

        def if_r(hr: r) -> goal:
            return p | (q | hr)

        return h.elim(if_p_or_q, if_r)

    result = or_assoc((p("hp") | q("hq")) | r("hr"))
    assert result.type == goal
    assert str(result) == "elim(elim(hp | (q | r)(), p() | (hq | r())), p() | (q() | hr))"


main()
