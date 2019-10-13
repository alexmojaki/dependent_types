import functools
import inspect


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

    def __init__(self, name=None, *, expr=None, universe=None):
        assert bool(name) ^ bool(universe)
        self.name = name
        if name:
            self.type = Type
        self.universe = universe
        self.expr = expr

    def __call__(self, name, expr=None):
        if expr is None:
            expr = FunctionApplication(self)
        result = Instance(self, name, expr)
        result.type = self
        return result

    type = TypeDescriptor()

    def __eq__(self, other):
        return (
                isinstance(other, BaseType)
                and self.universe == other.universe
                and self.expr == other.expr
        )


class Instance:
    def __init__(self, typ, name, expr):
        self.name = name
        self.type = typ
        self.expr = expr

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return (
                isinstance(other, Instance)
                and self.expr == other.expr
        )


class FunctionApplication:
    def __init__(self, *args):
        self.args = args

    def __eq__(self, other):
        return type(self) == type(other) and self.args == other.args


def autofunc(f):
    signature = inspect.signature(f)

    @functools.wraps(f)
    def func(*args):
        typ = signature.return_annotation
        name = f'{f.__name__}({", ".join(arg.name for arg in args)})'
        expr = FunctionApplication(f.__code__, *args)
        return typ(name, expr=expr)

    return check_types(func)


def check_types(f):
    signature = inspect.signature(f)
    types = [
        param.annotation for param in
        signature.parameters.values()
    ]

    @functools.wraps(f)
    def wrapper(*args):
        for typ, arg in zip(types, args):
            assert typ == arg.type

        result = f(*args)
        assert result.type == signature.return_annotation
        return result

    return wrapper


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

    @autofunc
    def f(a: A) -> B: ...

    @autofunc
    def g(b: B) -> C: ...

    @check_types
    def composed(a: A) -> C:
        return g(f(a))

    c = composed(A('a'))
    print(c)
    assert c.type is C

    test_dependant_types()


def test_dependant_types():
    """
    constant List   : Type → Type

    constant cons   : Π T : Type, T → List T → List T
    constant nil    : Π T : Type, List T
    constant head   : Π T : Type, List T → T
    constant tail   : Π T : Type, List T → List T
    constant append : Π T : Type, List T → List T → List T
    """

    @autofunc
    def List(T: Type) -> Type: ...

    def cons(T: Type):
        @autofunc
        def cons(t: T, lst: List(T)) -> List(T): ...

        return cons

    def nil(T: Type):
        return List(T)('nil')

    A = Type('A')
    a = A('a')
    print(cons(A)(a, cons(A)(a, nil(A))))


if __name__ == '__main__':
    main()
