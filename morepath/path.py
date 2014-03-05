from morepath import generic
from morepath.traject import Traject, ParameterFactory, Path
from morepath.error import DirectiveError

from reg import arginfo
from types import ClassType

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


def get_converters(arguments, converters,
                   converter_for_type, converter_for_value):
    """Get converters for arguments.

    Use explicitly supplied converter if available, otherwise ask
    app for converter for the default value of argument.
    """
    result = {}
    for name, value in arguments.items():
        # find explicit converter
        converter = converters.get(name, None)
        # if explicit converter is type, look it up
        if type(converter) in [type, ClassType]:
            converter = converter_for_type(converter)
        # if still no converter, look it up for value
        if converter is None:
            converter = converter_for_value(value)
        if converter is None:
            raise DirectiveError(
                "Cannot find converter for default value: %r (%s)" %
                (value, type(value)))
        result[name] = converter
    return result


def get_url_parameters(arguments, exclude):
    return {name: default for (name, default) in arguments.items() if
            name not in exclude}


def get_variables_func(arguments, exclude):
    names = [name for name in arguments.keys() if name not in exclude]
    return lambda model: {name: getattr(model, name) for
                          name in names}


def register_path(app, model, path, variables, converters, required,
                  model_factory, arguments=None):
    traject = app.traject

    converters = converters or {}
    if arguments is None:
        arguments = get_arguments(model_factory, SPECIAL_ARGUMENTS)
    converters = get_converters(arguments, converters,
                                app.converter_for_type,
                                app.converter_for_value)
    exclude = Path(path).variables()
    exclude.update(app.mount_variables())
    parameters = get_url_parameters(arguments, exclude)
    if required is None:
        required = set()
    required = set(required)
    parameter_factory = ParameterFactory(parameters, converters, required)

    if variables is None:
        variables = get_variables_func(arguments, app.mount_variables())

    traject.add_pattern(path, (model_factory, parameter_factory),
                        converters)
    traject.inverse(model, path, variables,
                    converters, list(parameters.keys()))

    def get_app(model):
        return app

    app.register(generic.app, [model], get_app)
