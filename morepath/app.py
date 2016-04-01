import dectate
from reg import CachingKeyLookup, Registry

from .request import Request
from . import compat
from .implicit import set_implicit
from .reify import reify


COMPONENT_CACHE_SIZE = 5000
ALL_CACHE_SIZE = 5000
FALLBACK_CACHE_SIZE = 5000


class RegRegistry(Registry):
    """A reg registry with a cached lookup.
    """
    @reify
    def lookup(self):
        return CachingKeyLookup(
            self,
            COMPONENT_CACHE_SIZE,
            ALL_CACHE_SIZE,
            FALLBACK_CACHE_SIZE).lookup()


class App(dectate.App):
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

    Subclasses from :class:`dectate.App`, which provides the
    :meth:`dectate.App.directive` decorator that lets you register
    new directives.
    """
    parent = None
    """The parent in which this app was mounted."""

    request_class = Request
    """The class of the Request to create. Must be a subclass of
    :class:`morepath.Request`.
    """

    logger_name = 'morepath.directive'

    def __init__(self):
        pass

    @reify
    def lookup(self):
        """Get the :class:`reg.Lookup` for this application.

        :returns: a :class:`reg.Lookup` instance.
        """
        # this in turn uses a cached lookup from the reg_registry
        # the caching happens on the reg_registry and not here to
        # ensure that each instance of App uses the same cache.
        return self.config.reg_registry.lookup

    def set_implicit(self):
        set_implicit(self.lookup)

    def request(self, environ):
        """Create a :class:`Request` given WSGI environment for this app.

        :param environ: WSGI environment
        :returns: :class:`morepath.Request` instance
        """
        return self.request_class(environ, self)

    def __call__(self, environ, start_response):
        """This app as a WSGI application.
        """
        request = self.request(environ)
        response = self.publish(request)
        return response(environ, start_response)

    def ancestors(self):
        """Return iterable of all ancestors of this app.

        Includes this app itself as the first ancestor, all the way
        up to the root app in the mount chain.
        """
        app = self
        while app is not None:
            yield app
            app = app.parent

    @reify
    def root(self):
        """The root application.
        """
        return list(self.ancestors())[-1]

    def child(self, app, **variables):
        """Get app mounted in this app.

        Either give it an instance of the app class as the first
        parameter, or the app class itself (or name under which it was
        mounted) as the first parameter and as ``variables`` the
        parameters that go to its ``mount`` function.

        Returns the mounted application object, with its ``parent``
        attribute set to this app object, or ``None`` if this
        application cannot be mounted in this one.
        """
        if isinstance(app, App):
            result = app
            # XXX assert that variables is empty

            # XXX do we need to deal with subclasses of apps?
            if app.__class__ not in self.config.path_registry.mounted:
                return None
        else:
            if isinstance(app, compat.string_types):
                factory = self.config.path_registry.named_mounted.get(app)
            else:
                factory = self.config.path_registry.mounted.get(app)
            if factory is None:
                return None
            result = factory(**variables)
        result.parent = self
        return result

    def sibling(self, app, **variables):
        """Get app mounted next to this app.

        Either give it an instance of the app class as the first
        parameter, or the app class itself (or name under which it was
        mounted) as the first parameter and as ``variables`` the
        parameters that go to its ``mount`` function.

        Returns the mounted application object, with its ``parent``
        attribute set to the same parent as this one, or ``None`` if such
        a sibling application does not exist.
        """
        parent = self.parent
        if parent is None:
            return None
        return parent.child(app, **variables)

    @reify
    def publish(self):
        # XXX import cycles...
        from .publish import publish
        result = publish
        for tween_factory in reversed(
                self.config.tween_registry.sorted_tween_factories()):
            result = tween_factory(self, result)
        return result

    @property
    def settings(self):
        """Returns the settings bound to this app.

        Works the same way as :func:`morepath.generic.settings`. Unlike calling
        ``morepath.settings`` however, this property does not rely on the
        global lookup. It's simply a shortcut to
        ``app.config.setting_registry``.

        """

        return self.config.setting_registry
