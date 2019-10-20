import inspect
import types
from types import SimpleNamespace


class TypeDescriptor:
    def __get__(self, instance, owner):
        if instance is None:
            return Type(universe=1)
        return Type(universe=instance.universe + 1)


class BaseType:
    universe = None
    name = None

    def __repr__(self):
        if self.universe == 0:
            return "Type"
        elif self.universe is None:
            return self.name
        else:
            return f"Type(universe={self.universe})"


class TypeMeta(BaseType, type):
    pass


class Type(BaseType, metaclass=TypeMeta):
    universe = 0

    def __init__(self, name=None, *, value=None, universe=None):
        assert bool(name) ^ bool(universe)
        self.name = name
        if name:
            self.type = Type
        self.universe = universe
        self.value = value or id(self)

    def __call__(self, name, value=None):
        result = Instance(self, name, value)
        result.type = self
        return result

    type = TypeDescriptor()

    def __eq__(self, other):
        return (
                isinstance(other, BaseType)
                and self.universe == other.universe
                and self.value == other.value
        )


class Arrow(Type):

    def __init__(self, signature: inspect.Signature, *args, **kwargs):
        # TODO name from signature
        params = tuple(param.annotation
                       for param in signature.parameters.values())
        return_annotation = signature.return_annotation

        value = (params, signature.return_annotation)

        super().__init__(name=f"{params} -> {return_annotation}", value=value, *args, **kwargs)
        self.signature = signature


class Instance:
    def __init__(self, typ, name, value):
        self.name = name
        self.type = typ
        self.value = value

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return (
                isinstance(other, Instance)
                and self.value == other.value
                and self.type == other.type
        )


class ArrowInstance(Instance):

    def __call__(self, *args, **kwargs):
        self.raise_on_param_type_error(*args, **kwargs)
        result = self.value(*args, **kwargs) if self.value else None

        if result is None:
            formatted_args = [
                *map(str, args),
                *[f"{k}={v}" for k, v in kwargs.items()]
            ]
            name = f"{self.name}({', '.join(formatted_args)})"
            result = self.type.signature.return_annotation(name, value=(self, args, kwargs))

        self.raise_on_result_type_error(result)
        return result

    def raise_on_param_type_error(self, *args, **kwargs):
        bound = self.type.signature.bind(*args, **kwargs)
        bound.apply_defaults()

        for name, val in bound.arguments.items():
            expected_type = self.type.signature.parameters[name].annotation
            assert val.type == expected_type

    def raise_on_result_type_error(self, result):
        assert result.type == self.type.signature.return_annotation


def arrow(f):
    signature = inspect.signature(f)
    f_type = Arrow(signature)
    return ArrowInstance(f_type, f.__name__, f)


def main():
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

    test_dependent_types()


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


if __name__ == '__main__':
    main()
