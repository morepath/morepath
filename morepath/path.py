"""Registration of routes.

This builds on :mod:`morepath.traject`.

See also :class:`morepath.directive.PathRegistry`
"""


from dectate import DirectiveError
from reg import arginfo, methodify
try:
    # Python 2
    from urllib import urlencode, quote
except ImportError:
    from urllib.parse import urlencode, quote


from .traject import Path as TrajectPath, TrajectRegistry
from .converter import ConverterRegistry, IDENTITY_CONVERTER
from .error import LinkError


SPECIAL_ARGUMENTS = ['request', 'app']


class PathRegistry(TrajectRegistry):
    """A registry for routes.

    Subclasses :class:`morepath.traject.TrajectRegistry`.

    Used by :meth:`morepath.App.path` and :meth:`morepath.App.mount`
    directives to register routes. Also used by the
    :meth:`morepath.App.defer_links` and
    :meth:`morepath.App.defer_class_links` directives.

    :param converter_registry: a
      :class:`morepath.directive.ConverterRegistry` instance

    """
    factory_arguments = {
        'converter_registry': ConverterRegistry
    }

    app_class_arg = True

    def __init__(self, app_class, converter_registry):
        super(PathRegistry, self).__init__()
        self.app_class = app_class
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

        info = arginfo(model_factory)
        if info.varargs is not None:
            raise DirectiveError(
                "Cannot use varargs in function signature: %s" %
                info.varargs)
        if info.keywords is not None:
            raise DirectiveError(
                "Cannot use keywords in function signature: %s" %
                info.keywords)

        path_variables = TrajectPath(path).variables()
        for path_variable in path_variables:
            if path_variable not in arguments:
                raise DirectiveError(
                    "Variable in path not found in function signature: %s"
                    % path_variable)

        parameters = filter_arguments(arguments, path_variables)

        if required is None:
            required = set()
        required = set(required)

        extra = 'extra_parameters' in arguments

        self.add_pattern(path, model_factory, parameters,
                         converters, absorb, required, extra)

        if variables is not None:
            self.register_path_variables(model, variables)

        self.register_inverse_path(model, path, arguments, converters,
                                   absorb)

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

    def register_path_variables(self, model, func):
        """Register variables function for a model class.

        :param model: model class
        :param func: function that gets a model instance argument and
          returns a variables dict.
        """
        self.app_class._path_variables.register(
            methodify(func, selfname='app'), obj=model)

    def register_inverse_path(self, model, path, factory_args,
                              converters=None, absorb=False):
        """Register information for link generation.

        :param model: model class
        :param path: the route
        :param factory_args: a list of the arguments of the factory
          function for this path.
        :param converters: a converters dict.
        :param absorb: bool, if true this is an absorbing path.
        """
        converters = converters or {}
        get_path = Path(path, factory_args, converters, absorb)

        self.app_class._class_path.register(get_path, model=model)

        def default_path_variables(app, obj):
            return {name: getattr(obj, name) for name in factory_args}

        self.app_class._default_path_variables.register(
            default_path_variables,
            obj=model)

    def register_defer_links(self, model, app_factory):
        """Register factory for app to defer links to.

        See :meth:`morepath.App.defer_links` for more information.

        :param model: model class to defer links for.
        :param app_factory: function that takes app instance and model
          object as arguments and should return another app instance that
          does the link generation.
        """
        self.app_class._deferred_link_app.register(
            app_factory,
            obj=model)

    def register_defer_class_links(self, model, get_variables, app_factory):
        """Register factory for app to defer class links to.

        See :meth:`morepath.App.defer_class_links` for more information.

        :param model: model class to defer links for.
        :param get_variables: get variables dict for obj.
        :param app_factory: function that model class, app instance
          and variables dict as arguments and should return another
          app instance that does the link generation.
        """
        self.register_path_variables(model, get_variables)
        self.app_class._deferred_class_link_app.register(
            app_factory,
            model=model)


class PathInfo(object):
    """Abstract representation of a path.

    :param path: a str representing a path
    :param parameters: a dict representing URL parameters.
    """
    def __init__(self, path, parameters):
        self.path = path
        self.parameters = parameters

    def url(self, prefix, name):
        """Turn a path into a URL.

        :param prefix: the URL prefix to put in front of the path. This
          should contain something like ``http://localhost``, so the URL
          without the path or parameter information.
        :param name: additional view name to postfix to the path.
        :return: a URL with the prefix, the name and URL encoded parameters.
        """
        parts = []
        if self.path:
            # explicitly define safe with ~ for a workaround
            # of this Python bug:
            # https://bugs.python.org/issue16285
            # tilde should not be encoded according to RFC3986
            parts.append(quote(self.path.encode('utf-8'), '/~'))
        if name:
            parts.append(name)
        # add prefix in the end. Even if result is empty we always get
        # a / at least
        result = prefix + '/' + '/'.join(parts)
        if self.parameters:
            parameters = dict((key, [v.encode('utf-8') for v in value])
                              for (key, value) in self.parameters.items())
            result += '?' + fixed_urlencode(parameters, True)
        return result


class Path(object):
    """Registered path for linking purposes.

    :param path: the route.
    :param factory_args: the arguments for the factory function used to
      construct this path. This is used to determine the URL parameters
      for the path.
    :param converters: converters dictionary that is used to represent
      variables in the path.
    :param absorb: bool indicating this is an absorbing path.
    """
    def __init__(self, path, factory_args, converters, absorb):
        self.path = path
        traject_path = TrajectPath(path)
        self.interpolation_path = traject_path.interpolation_str()
        path_variables = traject_path.variables()
        self.parameter_names = {name for name in factory_args if
                                name not in path_variables}
        self.converters = converters
        self.absorb = absorb

    def get_variables_and_parameters(self, variables, extra_parameters):
        """Get converted variables and parameters.

        :param variables: dict of variables to use in the path.
        :param extra_parameters: dict of additional parameters to use.
        :return: ``variables, parameters`` tuple with dicts of converted
          path variables and converted URL parameters.
        """
        converters = self.converters
        parameter_names = self.parameter_names
        path_variables = {}
        parameters = {}

        for name, value in variables.items():
            if name not in parameter_names:
                if value is None:
                    raise LinkError(
                        "Path variable %s for path %s is None" % (
                            name, self.path))
                path_variables[name] = converters.get(
                    name, IDENTITY_CONVERTER).encode(value)[0]
            else:
                if value is None or value == []:
                    continue
                parameters[name] = converters.get(
                    name, IDENTITY_CONVERTER).encode(value)
        if extra_parameters:
            for name, value in extra_parameters.items():
                parameters[name] = converters.get(
                    name, IDENTITY_CONVERTER).encode(value)
        return path_variables, parameters

    def __call__(self, app, model, variables):
        """Get path info given model and variables.

        :param app: the app instance. Not actually used in the
          implementation but passed if this is registered as a method.
        :param model: model class. Not actually used in the
          implementation but used for dispatch in
          :meth:`GenericApp._class_path`.
        :param variables: dict with the variables used in the path. each
          argument to the factory function should be represented.
        :return: :class:`PathInfo` instance representing the path.
        """
        if not isinstance(variables, dict):
            raise LinkError("Variables is not a dict: %r" % variables)
        extra_parameters = variables.pop('extra_parameters', None)
        if self.absorb:
            absorbed_path = variables.pop('absorb')
        else:
            absorbed_path = None

        path_variables, url_parameters = self.get_variables_and_parameters(
            variables, extra_parameters)

        path = self.interpolation_path % path_variables

        if absorbed_path is not None:
            if path:
                path += '/' + absorbed_path
            else:
                # when there is no path yet we are absorbing from
                # the root and we don't want an additional /
                path = absorbed_path
        return PathInfo(path, url_parameters)


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


def fixed_urlencode(s, doseq=0):
    """``urllib.urlencode`` fixed for ``~``

    Workaround for Python bug:

    https://bugs.python.org/issue16285

    tilde should not be encoded according to RFC3986
    """
    return urlencode(s, doseq).replace('%7E', '~')
