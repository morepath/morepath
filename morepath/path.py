from morepath import generic
from morepath.traject import Path, Inverse
from morepath.converter import ParameterFactory

from reg import arginfo

SPECIAL_ARGUMENTS = ['request', 'parent']


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


def register_path(app, model, path, variables, converters, required,
                  get_converters, absorb, model_factory, arguments=None):
    traject = app.traject

    converters = converters or {}
    if get_converters is not None:
        converters.update(get_converters())
    if arguments is None:
        arguments = get_arguments(model_factory, SPECIAL_ARGUMENTS)
    converters = app.argument_and_explicit_converters(arguments, converters)
    exclude = Path(path).variables()
    exclude.update(app.mount_variables())
    parameters = get_url_parameters(arguments, exclude)
    if required is None:
        required = set()
    required = set(required)
    parameter_factory = ParameterFactory(parameters, converters, required,
                                         'extra_parameters' in arguments)
    if variables is None:
        variables = get_variables_func(arguments, app.mount_variables())

    traject.add_pattern(path, (model_factory, parameter_factory),
                        converters, absorb)

    inverse = Inverse(path, variables, converters, parameters.keys(),
                      absorb)
    app.register(generic.path, [model], inverse)
