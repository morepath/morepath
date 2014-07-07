from .mount import Mount
from .action import FunctionAction
from .request import Request
from .traject import Traject
from .config import Configurable
from .settings import SettingSectionContainer
from .converter import ConverterRegistry
from .error import MountError
from .tween import TweenRegistry
from morepath import generic
from reg import ClassRegistry, Lookup, CachingClassLookup
import venusian
from .reify import reify
from .publish import publish


class Registry(Configurable, ClassRegistry, ConverterRegistry, TweenRegistry):
    def __init__(self, name, bases, testing_config, variables):
        self.name = name
        bases = [base.registry for base in bases if hasattr(base, 'registry')]
        ClassRegistry.__init__(self)
        Configurable.__init__(self, bases, testing_config)
        ConverterRegistry.__init__(self)
        TweenRegistry.__init__(self)
        self.settings = SettingSectionContainer()
        self._mounted = {}
        self.variables = variables
        self.clear()

    def actions(self):
        yield FunctionAction(self, generic.settings), lambda: self.settings

    def clear(self):
        """Clear all registrations in this application.
        """
        ClassRegistry.clear(self)
        Configurable.clear(self)
        ConverterRegistry.clear(self)
        TweenRegistry.clear(self)
        self.traject = Traject()
        self._mounted = {}

    @reify
    def lookup(self):
        return Lookup(CachingClassLookup(self))


def callback(scanner, name, obj):
    scanner.config.configurable(obj.registry)


class AppMeta(type):
    def __new__(mcl, name, bases, d):
        testing_config = d.get('testing_config')
        d['registry'] = Registry(name, bases, testing_config,
                                 d.get('variables', []))
        result = super(AppMeta, mcl).__new__(mcl, name, bases, d)
        venusian.attach(result, callback)
        return result


class App(object):
    """Base for application objects.

    App can be used as a WSGI application, i.e. it can be called
    with ``environ`` and ``start_response`` arguments.
    """
    testing_config = None
    variables = set()

    __metaclass__ = AppMeta

    def __init__(self, **context):
        self.settings = self.registry.settings

        for name in self.variables:
            if name not in context:
                raise MountError(
                    "Cannot mount app without context variable: %s" % name)
        self._app_mount = Mount(self, lambda: context, {})

    @reify
    def lookup(self):
        """Get the :class:`reg.Lookup` for this application.

        :returns: a :class:`reg.Lookup` instance.
        """
        return self.registry.lookup

    @reify
    def traject(self):
        return self.registry.traject

    # def set_implicit(self):
    #     """Set app's lookup as implicit reg lookup.

    #     Only does something if implicit mode is enabled. If disabled,
    #     has no effect.
    #     """

    def request(self, environ):
        """Create a :class:`Request` given WSGI environment.

        :param environ: WSGI environment
        :returns: :class:`morepath.Request` instance
        """
        request = Request(environ)
        request.lookup = self.lookup
        return request

    def __call__(self, environ, start_response):
        """This app as a WSGI application.

        This is only possible when the app expects no variables; if it
        does, use ``mount()`` to create a WSGI app first.
        """
        return self._app_mount(environ, start_response)

    # XXX can do this in init now
    @reify
    def publish(self):
        result = publish
        for tween_factory in reversed(self.registry.sorted_tween_factories()):
            result = tween_factory(self, result)
        return result


# class App(AppBase):
#     """A Morepath-based application object.

#     Extends :class:`AppBase` and through it
#     :class:`morepath.config.Configurable`, :class:`reg.ClassRegistry`
#     and :class:`morepath.converter.ConverterRegistry`.

#     You can configure an application using Morepath decorator directives.

#     An application can extend one or more other applications, if
#     desired.  All morepath App's descend from ``global_app`` however,
#     which contains the base configuration of the Morepath framework.

#     Conflicting configuration within an app is automatically
#     rejected. An extended app cannot conflict with the apps it is
#     extending however; instead configuration is overridden.
#     """
#     def __init__(self, name=None, extends=None, variables=None,
#                  testing_config=None):
#         """
#         :param name: A name for this application. This is used in
#           error reporting.
#         :type name: str
#         :param extends: :class:`App` objects that this
#           app extends/overrides.
#         :type extends: list, :class:`App` or ``None``
#         :param variables: variable names that
#           this application expects when mounted. Optional.
#         :type variables: list or set
#         :param testing_config: a :class:`morepath.Config` that actions
#           are added to directly, instead of waiting for
#           a scanning phase. This is handy during testing. If you want to
#           use decorators inline in a test function, supply a
#           ``testing_config``. It's not useful outside of tests. Optional.
#         """
#         if not extends:
#             extends = [global_app]
#         super(App, self).__init__(name, extends, variables, testing_config)
#         # XXX why does this need to be repeated?
#         venusian.attach(self, callback)



# global_app = AppBase('global_app')
# """The global app object.

# Instance of :class:`AppBase`.

# This is the application object that the Morepath framework is
# registered on. It's automatically included in the extends of any
# :class:`App`` object.

# You could add configuration to ``global_app`` but it is recommended
# you don't do so. Instead to extend or override the framework you can
# create your own :class:`App` with this additional configuration.
# """
