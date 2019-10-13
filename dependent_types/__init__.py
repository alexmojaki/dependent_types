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


if __name__ == '__main__':
    main()
