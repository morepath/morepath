"""Here we define the Morepath application class:
:class:`morepath.App`. The application class makes available the
directives to the developer. When instantiated it is a WSGI_
application that can be hooked into WSGI servers.

Because it is a :class:`dectate.App` subclass, the class object has
two special class attributes: :attr:`dectate.App.dectate`, which
contains Dectate internals, and :attr:`dectate.App.config` which
contains the actual configurations.

To actually serve requests it uses :func:`morepath.publish.publish`.

We also define a Reg registry that is used for generic function
configuration.

.. _WSGI: https://www.python.org/dev/peps/pep-3333
"""

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
    """A :class:`reg.Registry` with a cached lookup.

    Morepath uses Reg to implement generic function lookups which
    are used for various aspects of configuration, in particular
    view lookup.

    We cache the lookup using a :class:`reg.CachingKeyLookup` so that
    generic function lookups are faster.
    """
    @reify
    def lookup(self):
        """Cached :class:`reg.Lookup`

        Property is reified with :func:`morepath.reify.reify` so cache
        is shared between :class:`morepath.App` instances that use
        this registry.

        """
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

    You can turn your app class into a `WSGI`_ application by instantiating
    it. You can then call it with the ``environ`` and ``start_response``
    arguments.

    .. _`WSGI`: https://www.python.org/dev/peps/pep-3333/

    Subclasses from :class:`dectate.App`, which provides the
    :meth:`dectate.App.directive` decorator that lets you register
    new directives.
    """
    parent = None
    """The parent in which this app was mounted."""

    request_class = Request
    """The class of the Request to create. Must be a subclass of
    :class:`morepath.Request`.

    By default the request class is :class:`morepath.Request`
    """

    logger_name = 'morepath.directive'
    """Prefix used by dectate to log configuration actions.
    """

    def __init__(self):
        pass

    @reify
    def lookup(self):
        """Get the :class:`reg.Lookup` for this application.

        :return: a :class:`reg.Lookup` instance.
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
        :return: :class:`morepath.Request` instance
        """
        return self.request_class(environ, self)

    def __call__(self, environ, start_response):
        """This app as a WSGI application.

        See the WSGI_ spec for more information.

        Uses :meth:`App.request` to generate a
        :class:`morepath.Request` instance, then uses
        meth:`App.publish` get the :class:`morepath.Response`
        instance.

        :param environ: WSGI environment
        :param start_response: WSGI start_response
        :return: WSGI iterable.
        """
        request = self.request(environ)
        response = self.publish(request)
        return response(environ, start_response)

    @reify
    def publish(self):
        """Publish functionality wrapped in tweens.

        You can use middleware (:doc:`tweens`) that can hooks in
        before a request is passed into the application and just after
        the response comes out of the application. Here we use
        :meth:`morepath.tween.TweenRegistry.wrap` to wrap the
        :func:`morepath.publish.publish` function into the configured
        tweens.

        This property uses :func:`morepath.reify.reify` so that the
        tween wrapping only happens once when the first request is
        handled and is cached afterwards.

        :return: a function that a :class:`morepath.Request` instance
          and returns a :class:`morepath.Response` instance.

        """
        return self.config.tween_registry.wrap(self)

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

    @property
    def settings(self):
        """Returns the settings bound to this app.

        Works the same way as :func:`morepath.generic.settings`. Unlike calling
        ``morepath.settings`` however, this property does not rely on the
        global lookup.
        """
        return self.config.setting_registry

    @classmethod
    def commit(cls):
        """Commit the app, and recursively, the apps mounted under it.

        Mounted apps are discovered in breadth-first order.

        :return: the set of discovered apps.
        """

        discovery = set()
        found = {cls}
        while found:
            discovery.update(found)
            dectate.commit(*found)
            found = (
                {c for a in found for c in a.config.path_registry.mounted} -
                discovery)
        return discovery
