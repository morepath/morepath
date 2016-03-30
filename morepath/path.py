from morepath import generic
from morepath.traject import Path, Inverse
from morepath.converter import ParameterFactory
from dectate import DirectiveError

from reg import arginfo

SPECIAL_ARGUMENTS = ['request', 'app']


def get_arguments(callable, exclude):
    """Get dictionary with arguments and their default value.

    If no default is given, default value is taken to be None.
    """
    info = arginfo(callable)
    defaults = info.defaults or []
    defaults = [None] * (len(info.args) - len(defaults)) + list(defaults)
    return {name: default for (name, default) in zip(info.args, defaults)
            if name not in exclude}


def get_url_parameters(arguments, exclude):
    return {name: default for (name, default) in arguments.items() if
            name not in exclude}


def get_variables_func(arguments, exclude):
    names = [name for name in arguments.keys() if name not in exclude]
    return lambda model: {name: getattr(model, name) for
                          name in names}


def register_path(registry, converter_registry, model, path,
                  variables, converters, required, get_converters,
                  absorb, model_factory):
    traject = registry.traject

    converters = converters or {}
    if get_converters is not None:
        converters.update(get_converters())
    arguments = get_arguments(model_factory, SPECIAL_ARGUMENTS)
    converters = converter_registry.argument_and_explicit_converters(
        arguments, converters)
    path_variables = Path(path).variables()

    info = arginfo(model_factory)
    if info.varargs is not None:
        raise DirectiveError(
            "Cannot use varargs in function signature: %s" % info.varargs)
    if info.keywords is not None:
        raise DirectiveError(
            "Cannot use keywords in function signature: %s" % info.keywords)
    for path_variable in path_variables:
        if path_variable not in arguments:
            raise DirectiveError(
                "Variable in path not found in function signature: %s"
                % path_variable)

    parameters = get_url_parameters(arguments, path_variables)
    if required is None:
        required = set()
    required = set(required)
    parameter_factory = ParameterFactory(parameters, converters, required,
                                         'extra_parameters' in arguments)
    if variables is None:
        variables = get_variables_func(arguments, {})

    traject.add_pattern(path, (model_factory, parameter_factory),
                        converters, absorb)

    inverse = Inverse(path, variables, converters, parameters.keys(),
                      absorb)
    registry.register_function(generic.path, inverse, obj=model)

    def class_path(cls, variables):
        return inverse.with_variables(variables)
    registry.register_function(generic.class_path, class_path, cls=model)
