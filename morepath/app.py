from .publish import publish, Mount
from .request import Request
from .traject import Traject
from .config import Configurable
from reg import ClassRegistry, Lookup, CachingClassLookup
import venusian
from werkzeug.serving import run_simple
from morepath import generic


class AppBase(Configurable, ClassRegistry):
    """Base for application objects.

    The application base is split from the :class:`App`
    class so that we can have an :class:`App` class that automatically
    extends from ``global_app``, which defines the Morepath framework
    itself.  Normally you would use :class:`App` instead this one.
    """
    # XXX have a way to define parameters for app here
    def __init__(self, name='', extends=None):
        """
        :param name: A name for this application. This is used in
          error reporting.
        :type name: str
        :param extends: :class:`App` objects that this
          app extends/overrides.
        :type extends: list, :class:`App` or ``None``
        """
        ClassRegistry.__init__(self)
        Configurable.__init__(self, extends)
        self.name = name
        self.traject = Traject()
        self._cached_lookup = None
        # allow being scanned by venusian
        venusian.attach(self, callback)

    def __repr__(self):
        return '<morepath.App %r>' % self.name

    def clear(self):
        ClassRegistry.clear(self)
        Configurable.clear(self)
        self.traject = Traject()
        self._cached_lookup = None

    def lookup(self):
        if self._cached_lookup is not None:
            return self._cached_lookup
        self._cached_lookup = result = Lookup(CachingClassLookup(self))
        return result

    def request(self, environ):
        request = Request(environ)
        request.lookup = self.lookup()
        return request

    def context(self, **kw):
        def wsgi(environ, start_response):
            return self(environ, start_response, context=kw)
        return wsgi

    def mounted(self, context=None):
        context = context or {}
        return Mount(self, lambda: context, {})

    def __call__(self, environ, start_response, context=None):
        request = self.request(environ)
        response = publish(request, self.mounted(context))
        return response(environ, start_response)

    def run(self, host=None, port=None, **options):
        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = 5000
        run_simple(host, port, self, **options)


class App(AppBase):
    """A Morepath-based application object.

    Extends :class:`AppBase`.

    You can configure an application using Morepath decorator directives.

    An application can extend one or more other applications, if
    desired.  All morepath App's descend from ``global_app`` however,
    which contains the base configuration of the Morepath framework.

    Conflicting configuration within an app is automatically
    rejected. An extended app cannot conflict with the apps it is
    extending however; instead configuration will be considered to be
    overridden.
    """
    def __init__(self, name='', extends=None):
        """
        :param name: A name for this application. This is used in
          error reporting.
        :type name: str
        :param extends: :class:`App` objects that this
          app extends/overrides.
        :type extends: list, :class:`App` or ``None``
        """
        if not extends:
            extends = [global_app]
        super(App, self).__init__(name, extends)
        # XXX why does this need to be repeated?
        venusian.attach(self, callback)


def callback(scanner, name, obj):
    scanner.config.configurable(obj)


global_app = AppBase('global_app')
"""The global app object.

Instance of :class:`AppBase`.

This is the application object that the Morepath framework is
registered on. It's automatically included in the extends of any
:class:`App`` object.

You could add configuration to ``global_app`` but it is recommended
you don't do so. Instead to extend or override the framework you can
create your own :class:`App` with this additional configuration.
"""
