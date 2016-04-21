try:
    from urllib.parse import urlencode, quote
except ImportError:
    # Python 2
    from urllib import urlencode, quote

from .cachingreg import RegRegistry
from . import generic
from .converter import ConverterRegistry, IDENTITY_CONVERTER
from .error import LinkError
from .traject import Path as TrajectPath


class PathInfo(object):
    def __init__(self, path, parameters):
        self.path = path
        self.parameters = parameters

    def url(self, prefix, name):
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
    def __init__(self, path, factory_args, converters, absorb):
        self.path = path
        traject_path = TrajectPath(path)
        self.interpolation_path = traject_path.interpolation_str()
        self.factory_args = factory_args
        path_variables = traject_path.variables()
        self.parameter_names = {name for name in factory_args if
                                name not in path_variables}
        self.converters = converters
        self.absorb = absorb

    def get_variables_and_parameters(self, variables, extra_parameters):
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

    def __call__(self, model, variables):
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


class LinkRegistry(object):
    factory_arguments = {
        'reg_registry': RegRegistry,
        'converter_registry': ConverterRegistry
    }

    def __init__(self, reg_registry, converter_registry):
        self.reg_registry = reg_registry
        self.converter_registry = converter_registry

    def register_path_variables(self, model, func):
        self.reg_registry.register_function(generic.path_variables,
                                            func,
                                            obj=model)

    def register_path(self, model, path, factory_args,
                      converters=None, absorb=False):
        converters = converters or {}
        get_path = Path(path, factory_args, converters, absorb)

        self.reg_registry.register_function(generic.class_path, get_path,
                                            model=model)

        def default_path_variables(obj):
            return {name: getattr(obj, name) for name in factory_args}
        self.reg_registry.register_function(generic.default_path_variables,
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
        self.reg_registry.register_function(
            generic.deferred_link_app, app_factory,
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

        self.reg_registry.register_function(
            generic.deferred_class_link_app, app_factory,
            model=model)


def follow_defers(find, app, obj):
    """Resolve to deferring app and find something.

    For ``obj``, look up deferring app as defined by
    :class:`morepath.App.defer_links` recursively. Use the
    supplied ``find`` function to find something for ``obj`` in
    that app. When something found, return what is found and
    the app where it was found.

    :param find: a function that takes an ``app`` and ``obj`` parameter and
      should return something when it is found, or ``None`` when not.
    :param app: the :class:`morepath.App` instance to start looking
    :param obj: the model object to find things for.
    :return: a tuple with the thing found (or ``None``) and the app in
      which it was found.
    """
    seen = set()
    while app is not None:
        if app in seen:
            raise LinkError("Circular defer. Cannot link to: %r" % obj)
        result = find(app, obj)
        if result is not None:
            return result, app
        seen.add(app)
        next_app = generic.deferred_link_app(app, obj, lookup=app.lookup)
        if next_app is None:
            # only if we can establish the variables of the app here
            # fall back on using class link app
            variables = generic.path_variables(obj, lookup=app.lookup)
            if variables is not None:
                next_app = generic.deferred_class_link_app(
                    app, obj.__class__, variables, lookup=app.lookup)
        app = next_app
    return None, app


def follow_class_defers(find, app, model, variables):
    """Resolve to deferring app and find something.

    For ``model`` and ``variables``, look up deferring app as defined
    by :class:`morepath.App.defer_class_links` recursively. Use the
    supplied ``find`` function to find something for ``model`` and
    ``variables`` in that app. When something found, return what is
    found and the app where it was found.

    :param find: a function that takes an ``app``, ``model`` and
      ``variables`` arguments and should return something when it is
      found, or ``None`` when not.
    :param app: the :class:`morepath.App` instance to start looking
    :param model: the model class to find things for.
    :return: a tuple with the thing found (or ``None``) and the app in
      which it was found.
    """
    seen = set()
    while app is not None:
        if app in seen:
            raise LinkError("Circular defer. Cannot link to: %r" % model)
        result = find(app, model, variables)
        if result is not None:
            return result, app
        seen.add(app)
        app = generic.deferred_class_link_app(app, model, variables,
                                              lookup=app.lookup)
    return None, app


def fixed_urlencode(s, doseq=0):
    """``urllib.urlencode`` fixed for ``~``

    Workaround for Python bug:

    https://bugs.python.org/issue16285

    tilde should not be encoded according to RFC3986
    """
    return urlencode(s, doseq).replace('%7E', '~')
