import inspect
import types
from types import SimpleNamespace

from dependent_types.arrows import arrow, Arrow, ArrowInstance
from dependent_types.core import Type
from dependent_types.props import Prop, AndInstance, And


def test_basics():
    T = Type('T')
    t = T('t')
    assert str(t) == "t"
    assert str(T) == "T"
    assert str(Type) == "Type"
    assert str(Type.type) == "Type(universe=1)"
    assert str(Type.type.type) == "Type(universe=2)"

    assert t.type is T
    assert T.type is Type
    assert Type.universe == 0
    assert Type.type.universe == 1
    assert Type.type.type.universe == 2

    S = Type(universe=2)('S')
    assert str(S) == "S"
    assert str(S.type) == "Type(universe=2)"
    assert S.type.universe == 2

    A = Type('A')
    B = Type('B')
    C = Type('C')

    @arrow
    def f(a: A) -> B: ...

    @arrow
    def g(b: B) -> C: ...

    params = (inspect.Parameter("a", kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=A),)
    expected_sig = inspect.Signature(params, return_annotation=B)

    assert isinstance(f, ArrowInstance)
    assert f.type == Arrow(expected_sig)
    assert f.type.value == ((A,), B)
    assert isinstance(f.value, types.FunctionType)
    assert f.name == "f"

    a = A("a")
    b = f(a)
    c = g(b)
    assert str(b) == "f(a)"
    assert b.type is B
    assert str(c) == "g(f(a))"
    assert c.type is C


def test_dependent_types():
    """
    constant List   : Type → Type

    constant cons   : Π T : Type, T → List T → List T
    constant nil    : Π T : Type, List T
    constant head   : Π T : Type, List T → T
    constant tail   : Π T : Type, List T → List T
    constant append : Π T : Type, List T → List T → List T
    """

    @arrow
    def List(T: Type) -> Type: ...

    def lists(T: Type):
        @arrow
        def cons(t: T, lst: List(T)) -> List(T): ...

        @arrow
        def nil() -> List(T): ...

        @arrow
        def head(lst: List(T)) -> T: ...

        @arrow
        def tail(lst: List(T)) -> List(T): ...

        @arrow
        def append(lst1: List(T), lst2: List(T)) -> List(T): ...

        return SimpleNamespace(**locals())

    A = Type('A')
    assert List(A).type == Type

    a = A('a')
    L = lists(A)

    assert L.nil.name == "nil"
    assert str(L.nil.type) == "() -> List(A)"
    assert L.nil().type == List(A)

    assert str(L.head(L.tail(L.cons(a, L.append(List(A)('lst'), L.nil()))))) == \
           "head(tail(cons(a, append(lst, nil()))))"

    @arrow
    def List2(T: Type) -> Type: ...

    B = Type('B')

    assert List(A) == List(A)
    assert List(B) == List(B)
    assert List(A) != List(B)

    assert List2(A) == List2(A)
    assert List(A) != List2(A)


def test_props_basics():
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
