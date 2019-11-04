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
            return self.__name__
        elif self.universe is None:
            return self.name
        else:
            return f"Type(universe={self.universe})"


class TypeMeta(BaseType, type):
    pass


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


class Type(BaseType, metaclass=TypeMeta):
    universe = 0
    instance_class = Instance

    def __init__(self, name=None, value=None, universe=None):
        assert bool(name) ^ bool(universe)
        self.name = name
        if name:
            self.type = type(self)
        self.universe = universe
        self.value = value or id(self)

    def __call__(self, name, value=None):
        result = self.instance_class(self, name, value)
        result.type = self
        return result

    type = TypeDescriptor()

    def __eq__(self, other):
        return (
                isinstance(other, BaseType)
                and self.universe == other.universe
                and self.value == other.value
        )
