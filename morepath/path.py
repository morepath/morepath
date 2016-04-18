"""Registration of routes.

This builds on :mod:`morepath.traject`.
"""


from dectate import DirectiveError
from reg import arginfo

from .app import RegRegistry
from . import generic
from .traject import Path, Inverse, TrajectRegistry
from .converter import ParameterFactory, ConverterRegistry


SPECIAL_ARGUMENTS = ['request', 'app']


def get_arguments(callable, exclude):
    """Introspect callable to get callable arguments and their defaults.

    :param callable: callable object such as a function.
    :param exclude: a set of names not to extract.
    :return: a dict with as keys the argument names and as values the
       default values (or ``None`` if no default value was defined).
    """
    info = arginfo(callable)
    defaults = info.defaults or []
    defaults = [None] * (len(info.args) - len(defaults)) + list(defaults)
    return {name: default for (name, default) in zip(info.args, defaults)
            if name not in exclude}


def filter_arguments(arguments, exclude):
    """Filter arguments.

    Given a dictionary with arguments and defaults, filter out
    arguments in ``exclude``.

    :param arguments: arguments dict
    :param exclude: set of argument names to exclude.
    :return: filtered arguments dict
    """
    return {name: default for (name, default) in arguments.items() if
            name not in exclude}


def get_variables_func(arguments, exclude):
    """Create default variables function.

    The :meth:`morepath.App.path` directive uses this if no ``variables``
    function was defined by the user.

    :param arguments: arguments dictionary
    :param exclude: set of argument names to exclude.
    :return: a function that given a model instance returns a variables
       dict.
    """
    names = [name for name in arguments.keys() if name not in exclude]
    return lambda obj: {name: getattr(obj, name) for
                        name in names}


class PathRegistry(TrajectRegistry):
    """A registry for routes.

    Subclasses :class:`morepath.traject.TrajectRegistry`.

    Used by :meth:`morepath.App.path` and :meth:`morepath.App.mount`
    directives to register routes. Also used byt he
    :meth:`morepath.App.defer_links` directive.

    :param reg_registry: a :class:`reg.Registry` instance.
    :param converter_registry: a
      :class:`morepath.converter.ConverterRegistry` instance
    """
    factory_arguments = {
        'reg_registry': RegRegistry,
        'converter_registry': ConverterRegistry
    }

    def __init__(self, reg_registry, converter_registry):
        super(PathRegistry, self).__init__()
        self.reg_registry = reg_registry
        self.converter_registry = converter_registry
        self.mounted = {}
        self.named_mounted = {}

    def register_path(self, model, path,
                      variables, converters, required, get_converters,
                      absorb, model_factory):
        """Register a route.

        See :meth:`morepath.App.path` for more information.

        :param model: model class
        :param path: route
        :param variables: function that given model instance extracts
          dictionary with variables used in path and URL parameters.
        :param converters: converters structure
        :param required: required URL parameters
        :param get_converters: get a converter dynamically.
        :param absorb: absorb path
        :param model_factory: function that constructs model object given
          variables extracted from path and URL parameters.
        """
        converters = converters or {}
        if get_converters is not None:
            converters.update(get_converters())
        arguments = get_arguments(model_factory, SPECIAL_ARGUMENTS)
        converters = self.converter_registry.argument_and_explicit_converters(
            arguments, converters)
        path_variables = Path(path).variables()

        info = arginfo(model_factory)
        if info.varargs is not None:
            raise DirectiveError(
                "Cannot use varargs in function signature: %s" %
                info.varargs)
        if info.keywords is not None:
            raise DirectiveError(
                "Cannot use keywords in function signature: %s" %
                info.keywords)
        for path_variable in path_variables:
            if path_variable not in arguments:
                raise DirectiveError(
                    "Variable in path not found in function signature: %s"
                    % path_variable)

        parameters = filter_arguments(arguments, path_variables)
        if required is None:
            required = set()
        required = set(required)
        parameter_factory = ParameterFactory(parameters, converters, required,
                                             'extra_parameters' in arguments)
        if variables is None:
            variables = get_variables_func(arguments, {})

        self.add_pattern(path, (model_factory, parameter_factory),
                         converters, absorb)

        inverse = Inverse(path, variables, converters, parameters.keys(),
                          absorb)
        self.reg_registry.register_function(generic.path, inverse, obj=model)

        def class_path(cls, variables):
            return inverse.with_variables(variables)
        self.reg_registry.register_function(
            generic.class_path, class_path, cls=model)

    def register_mount(self, app, path, variables, converters, required,
                       get_converters, mount_name, app_factory):
        """Register a mounted app.

        See :meth:`morepath.App.mount` for more information.

        :param app: :class:`morepath.App` subclass.
        :param path: route
        :param variables: function that given model instance extracts
          dictionary with variables used in path and URL parameters.
        :param converters: converters structure
        :param required: required URL parameters
        :param get_converters: get a converter dynamically.
        :param mount_name: explicit name of this mount
        :param app_factory: function that constructs app instance given
          variables extracted from path and URL parameters.
        """
        self.register_path(app, path, variables,
                           converters, required, get_converters, False,
                           app_factory)

        self.mounted[app] = app_factory
        mount_name = mount_name or path
        self.named_mounted[mount_name] = app_factory

    def register_defer_links(self, model, app_factory):
        """Register factory for app to defer links to.

        See :meth:`morepath.App.defer_links` for more information.

        :param model: model class to defer links for.
        :param app_factory: function to get app instance that
          handles link generation.
        """
        self.reg_registry.register_function(
            generic.deferred_link_app, app_factory,
            obj=model)
