from functools import update_wrapper
from morepath import generic
from reg import ClassRegistry, Lookup, CachingClassLookup
import venusian

from . import compat
from .action import FunctionAction
from .compat import with_metaclass
from .config import Configurable
from .converter import ConverterRegistry
from .implicit import set_implicit
from .mount import MountRegistry
from .reify import reify
from .request import Request
from .settings import SettingSectionContainer
from .traject import Traject
from .tween import TweenRegistry


class Registry(Configurable, ClassRegistry, MountRegistry,
               ConverterRegistry, TweenRegistry):
    """A registry holding an application's configuration.
    """
    def __init__(self, name, bases, testing_config):
        self.name = name
        bases = [base.registry for base in bases if hasattr(base, 'registry')]
        ClassRegistry.__init__(self)
        MountRegistry.__init__(self)
        Configurable.__init__(self, bases, testing_config)
        ConverterRegistry.__init__(self)
        TweenRegistry.__init__(self)
        self.settings = SettingSectionContainer()
        self.clear()

    def actions(self):
        yield FunctionAction(self, generic.settings), lambda: self.settings

    def clear(self):
        """Clear all registrations in this application.
        """
        ClassRegistry.clear(self)
        MountRegistry.clear(self)
        Configurable.clear(self)
        ConverterRegistry.clear(self)
        TweenRegistry.clear(self)
        self.traject = Traject()

    @reify
    def lookup(self):
        return Lookup(CachingClassLookup(self))


def callback(scanner, name, obj):
    scanner.config.configurable(obj.registry)


class AppMeta(type):
    def __new__(cls, name, bases, d):
        testing_config = d.get('testing_config')
        d['registry'] = Registry(name, bases, testing_config)
        result = super(AppMeta, cls).__new__(cls, name, bases, d)
        venusian.attach(result, callback)
        return result


class App(with_metaclass(AppMeta)):
    """A Morepath-based application object.

    You subclass App to create a morepath application class. You can
    then configure this class using Morepath decorator directives.

    An application can extend one or more other applications, if
    desired, by subclassing them. By subclassing App itself, you get
    the base configuration of the Morepath framework itself.

    Conflicting configuration within an app is automatically
    rejected. An subclass app cannot conflict with the apps it is
    subclassing however; instead configuration is overridden.

    You can turn your app class into a WSGI application by instantiating
    it. You can then call it with the ``environ`` and ``start_response``
    arguments.
    """
    testing_config = None
    parent = None

    def __init__(self):
        pass

    @reify
    def lookup(self):
        """Get the :class:`reg.Lookup` for this application.

        :returns: a :class:`reg.Lookup` instance.
        """
        return self.registry.lookup

    def set_implicit(self):
        set_implicit(self.lookup)

    @reify
    def traject(self):
        return self.registry.traject

    def request(self, environ):
        """Create a :class:`Request` given WSGI environment.

        :param environ: WSGI environment
        :returns: :class:`morepath.Request` instance
        """
        request = Request(environ)
        request.app = self
        request.lookup = self.lookup
        return request

    def __call__(self, environ, start_response):
        """This app as a WSGI application.
        """
        request = self.request(environ)
        response = self.publish(request)
        return response(environ, start_response)

    def child(self, app, **variables):
        if isinstance(app, App):
            result = app
            # XXX assert that variables is empty

            # XXX do we need to deal with subclasses of apps?
            if app.__class__ not in self.registry.mounted:
                return None
        else:
            if isinstance(app, compat.string_types):
                factory = self.registry.named_mounted.get(app)
            else:
                factory = self.registry.mounted.get(app)
            if factory is None:
                return None
            result = factory(**variables)
        result.parent = self
        return result

    @reify
    def publish(self):
        # XXX import cycles...
        from .publish import publish
        result = publish
        for tween_factory in reversed(self.registry.sorted_tween_factories()):
            result = tween_factory(self, result)
        return result

    @classmethod
    def directive(cls, name):
        """Decorator to register a new directive with this application class.

        You use this as a class decorator for a :class:`morepath.Directive`
        subclass::

           @app.directive('my_directive')
           class FooDirective(morepath.Directive):
               ...

        This needs to be executed *before* the directive is being used
        and thus might introduce import dependency issues unlike
        normal Morepath configuration, so beware! An easy way to make
        sure that all directives are installed before you use them is
        to make sure you define them in the same module as where you
        define the application class that has them.
        """
        return DirectiveDirective(cls, name)


class DirectiveDirective(object):
    def __init__(self, cls, name):
        self.cls = cls
        self.name = name

    def __call__(self, directive):
        def method(self, *args, **kw):
            return directive(self, *args, **kw)
        # this is to help morepath.sphinxext to do the right thing
        method.actual_directive = directive
        update_wrapper(method, directive.__init__)
        setattr(self.cls, self.name, classmethod(method))
        return directive
