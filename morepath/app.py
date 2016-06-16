"""Here we define the Morepath application class:
:class:`morepath.App`. The application class makes available the
directives to the developer. When instantiated it is a WSGI_
application that can be hooked into WSGI servers.

Because it is a :class:`dectate.App` subclass, the class object has
two special class attributes: :attr:`dectate.App.dectate`, which
contains Dectate internals, and :attr:`dectate.App.config` which
contains the actual configurations.

To actually serve requests it uses :func:`morepath.publish.publish`.

.. _WSGI: https://www.python.org/dev/peps/pep-3333

Entirely documented in :class:`morepath.App` in the public API.
"""

import dectate

from .request import Request
from . import compat
from .implicit import set_implicit
from .reify import reify
from . import generic
from .path import PathInfo
from .error import LinkError


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
        if not self.is_committed():
            self.commit()
        return self.config.reg_registry.caching_lookup

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
    def mounted_app_classes(cls, callback=None):
        """Returns a set of this app class and any mounted under it.

        This assumes all app classes involved have already been
        committed previously, for instance by
        :meth:`morepath.App.commit`.

        Mounted apps are discovered in breadth-first order.

        The optional ``callback`` argument is used to implement
        :meth:`morepath.App.commit`.

        :param callback: a function that is called with app classes as
          its arguments. This can be used to do something with the app
          classes when they are first discovered, like commit
          them. Optional.
        :return: the set of app classes.

        """
        discovery = set()
        found = {cls}
        while found:
            discovery.update(found)
            if callback is not None:
                callback(*found)
            found = (
                {c for a in found for c in a.config.path_registry.mounted} -
                discovery)
        return discovery

    @classmethod
    def commit(cls):
        """Commit the app, and recursively, the apps mounted under it.

        Mounted apps are discovered in breadth-first order.

        :return: the set of discovered app clasess.
        """
        return cls.mounted_app_classes(dectate.commit)

    @classmethod
    def init_settings(cls, settings):
        """Pre-fill the settings before the app is started.

        Add settings to App, which can act as normal, can be overridden, etc.

        :param settings: a dictionary of setting sections which contain
          dictionaries of settings.
        """
        def set_setting_section(section, section_settings):
            cls.setting_section(section)(lambda: section_settings)

        for section, section_settings in settings.items():
            set_setting_section(section, section_settings)

    def _get_class_path(self, model, variables):
        """Path for a model class and variables.

        Only includes path within the current app, does not take
        mounting into account.

        :param model: model class
        :param variables: dict with variables to use in the path
        :return: a :class:`morepath.path.PathInfo` with path within this app.
        """
        return generic.class_path(model, variables, lookup=self.lookup)

    def _get_path(self, obj):
        """Path for a model obj.

        Only includes path within the current app, does not take
        mounting into account.

        :param obj: model object
        :return: a :class:`morepath.path.PathInfo` with path within this app.
        """
        return self._get_class_path(
            obj.__class__, generic.path_variables(obj, lookup=self.lookup))

    def _get_mounted_path(self, obj):
        """Path for model obj including mounted path.

        Includes path to this app itself, so takes mounting into account.

        :param obj: model object (or :class:`morepath.App` instance).
        :return: a :class:`morepath.path.PathInfo` with fully resolved
          path in mounts.
        """
        paths = []
        parameters = {}
        app = self
        while app is not None:
            info = app._get_path(obj)
            if info is None:
                return None
            paths.append(info.path)
            parameters.update(info.parameters)
            obj = app
            app = app.parent
        paths.reverse()
        return PathInfo('/'.join(paths).strip('/'), parameters)

    def _get_mounted_class_path(self, model, variables):
        """Path for model class and variables including mounted path.

        Includes path to this app itself, so takes mounting into account.

        :param model: model class
        :param variables: dict with variables to use in the path
        :return: a :class:`morepath.path.PathInfo` with fully resolved
          path in mounts.
        """
        info = self._get_class_path(model, variables)
        if info is None:
            return None
        if self.parent is None:
            return info
        mount_info = self.parent._get_mounted_path(self)
        path = mount_info.path
        if info.path:
            path += '/' + info.path
        parameters = info.parameters.copy()
        parameters.update(mount_info.parameters)
        return PathInfo(path, parameters)

    def _get_deferred_mounted_path(self, obj):
        """Path for obj taking into account deferring apps.

        Like :meth:`morepath.App._get_mounted_path` but takes
        :meth:`morepath.App.defer_links` and
        :meth:`morepath.App.defer_class_links` directives into
        account.
        """
        def find(app, obj):
            return app._get_mounted_path(obj)
        info, app = self._follow_defers(find, obj)
        return info

    def _get_deferred_mounted_class_path(self, model, variables):
        """Path for model and variables taking into account deferring apps.

        Like :meth:`morepath.App._get_mounted_class_path` but takes
        :meth:`morepath.App.defer_class_links` directive into
        account.
        """
        def find(app, model, variables):
            return app._get_mounted_class_path(model, variables)
        info, app = self._follow_class_defers(find, model, variables)
        return info

    def _follow_defers(self, find, obj):
        """Resolve to deferring app and find something.

        For ``obj``, look up deferring app as defined by
        :class:`morepath.App.defer_links` recursively. Use the
        supplied ``find`` function to find something for ``obj`` in
        that app. When something found, return what is found and
        the app where it was found.

        :param find: a function that takes an ``app`` and ``obj`` parameter and
          should return something when it is found, or ``None`` when not.
        :param obj: the model object to find things for.
        :return: a tuple with the thing found (or ``None``) and the app in
          which it was found.
        """
        seen = set()
        app = self
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

    def _follow_class_defers(self, find, model, variables):
        """Resolve to deferring app and find something.

        For ``model`` and ``variables``, look up deferring app as defined
        by :class:`morepath.App.defer_class_links` recursively. Use the
        supplied ``find`` function to find something for ``model`` and
        ``variables`` in that app. When something found, return what is
        found and the app where it was found.

        :param find: a function that takes an ``app``, ``model`` and
          ``variables`` arguments and should return something when it is
          found, or ``None`` when not.
        :param model: the model class to find things for.
        :return: a tuple with the thing found (or ``None``) and the app in
          which it was found.
        """
        seen = set()
        app = self
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

    def remember_identity(self, response, request, identity):
        """Modify response so that identity is remembered by client.

        :param response: :class:`morepath.Response` to remember identity on.
        :param request: :class:`morepath.Request`
        :param identity: :class:`morepath.Identity`
        """
        return self.config.identity_policy_registry.identity_policy.remember(
            response, request, identity)

    def forget_identity(self, response, request):
        """Modify response so that identity is forgotten by client.

        :param response: :class:`morepath.Response` to forget identity on.
        :param request: :class:`morepath.Request`
        """
        return self.config.identity_policy_registry.identity_policy.forget(
            response, request)
