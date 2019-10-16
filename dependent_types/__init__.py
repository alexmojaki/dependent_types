import functools
import inspect
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
        self.value = value

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
    def __init__(self, signature : inspect.Signature, *args, **kwargs):
        # TODO name from signature
        params = tuple( param.annotation 
            for param in signature.parameters.values() )
        return_annotation = signature.return_annotation
        
        value = (params, signature.return_annotation)
        
        super().__init__(name=f" {params} -> {return_annotation}", value=value, *args, **kwargs) 
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
        )


class ArrowInstance(Instance):
    def __call__(self, *args, **kwargs):
        self.raise_on_param_type_error(*args, **kwargs)
        result = None
        if self.value:
            result = self.value(*args, **kwargs)

        if result is None:
            result = self.type.signature.return_annotation(f"{self.name}( *{args}, **{kwargs} )")

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
    print(t)
    print(T)
    print(T.type)
    print(T.type.type)
    print(T.type.type.type)

    assert t.type is T
    assert T.type is Type
    assert Type.universe == 0
    assert Type.type.universe == 1
    assert Type.type.type.universe == 2

    S = Type(universe=2)('S')
    print(S)
    print(S.type)
    assert S.type.universe == 2

    A = Type('A')
    B = Type('B')
    C = Type('C')

    @arrow
    def f(a: A) -> B: ...

    @arrow
    def g(b: B) -> C: ...


    params = (inspect.Parameter("a", kind = inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=A),)
    expected_sig = inspect.Signature( params, return_annotation=B)
    print(f)
    print(f.type.value)
    print(Arrow( expected_sig ).value)
    assert f.type == Arrow( expected_sig )
    a = A("a")
    f(a)

    a = A("a")
    b = f(a)
    c = g(f(a))
    print(b)
    assert b.type is B
    print(c)
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
        def nil() -> List(T): 
            return List(T)('nil')

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

    print(L.nil.type)
    assert L.nil().type == List(A)

    print(L.head(L.tail(L.cons(a, L.append(List(A)('lst'), L.nil())))))


if __name__ == '__main__':
    main()
