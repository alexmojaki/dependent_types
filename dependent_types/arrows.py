import inspect
from inspect import Signature

from dependent_types.core import Instance, Type


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
            result = self.type.signature.return_annotation(name, value=(result, self, args, kwargs))

        self.raise_on_result_type_error(result)
        return result

    def raise_on_param_type_error(self, *args, **kwargs):
        bound = self.type.signature.bind(*args, **kwargs)
        bound.apply_defaults()

        for name, val in bound.arguments.items():
            expected_type = self.type.signature.parameters[name].annotation
            if val.type != expected_type:
                raise TypeError(f"{val} has type {val.type} instead of {expected_type}")

    def raise_on_result_type_error(self, result):
        expected_type = self.type.signature.return_annotation
        if expected_type is not Signature.empty:
            assert result.type == expected_type



class Arrow(Type):
    type = Type
    instance_class = ArrowInstance

    def __init__(self, signature: inspect.Signature, *args, **kwargs):
        params = tuple(param.annotation
                       for param in signature.parameters.values())
        return_annotation = signature.return_annotation

        value = (params, signature.return_annotation)

        super().__init__(name=f"{signature}", value=value, *args, **kwargs)
        self.signature = signature


def arrow(f):
    signature = inspect.signature(f)
    f_type = Arrow(signature)
    return f_type(name=f.__name__, value=f)


