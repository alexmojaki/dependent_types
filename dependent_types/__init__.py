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

    def __init__(self, name=None, *, universe=None):
        assert bool(name) ^ bool(universe)
        self.name = name
        if name:
            self.type = Type
        self.universe = universe

    def __call__(self, name):
        result = Instance(self, name)
        result.type = self
        return result

    type = TypeDescriptor()


class Instance:
    def __init__(self, typ, name):
        self.name = name
        self.type = typ

    def __repr__(self):
        return self.name


def autofunc(f):
    signature = inspect.signature(f)

    @functools.wraps(f)
    def func(*args):
        typ = signature.return_annotation
        name = f'{f.__name__}({", ".join(arg.name for arg in args)})'
        return typ(name)

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


if __name__ == '__main__':
    main()
