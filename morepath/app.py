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

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from typing import NoReturn as Never
from typing import TypeVar, overload

from webob.exc import HTTPNotFound

import dectate
import reg
from dectate import directive

from . import directive as action
from .error import LinkError
from .path import PathInfo
from .reify import reify
from .request import Request

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator
    from typing_extensions import Self

    from webob.response import Response as BaseResponse

    from reg.cache import DictCachingKeyLookup
    from reg.predicate import Predicate
    from reg.types import GetKeyLookup, KeyLookup

    from .authentication import Identity, NoIdentity
    from .settings import SettingRegistry
    from .tween import TweenRegistry
    from .types import AnyRequest, StartResponse, SupportsItems, WSGIEnvironment

_T = TypeVar("_T")
_AppT = TypeVar("_AppT", bound="App")


def cached_key_lookup(key_lookup: KeyLookup) -> DictCachingKeyLookup:
    return reg.DictCachingKeyLookup(key_lookup)


def commit_if_needed(app: App) -> None:
    if not app.is_committed():
        app.commit()


def dispatch_method(
    *predicates: str | Predicate,
    get_key_lookup: GetKeyLookup = cached_key_lookup,
    first_invocation_hook: Callable[[Any], object] = commit_if_needed,
    # NOTE: We keep allowing arbitrary keyword arguments at runtime
    #       for now, but type checkers should emit an error for these.
    **kw: Never,
) -> reg.dispatch_method[Any, Any, Any]:
    return reg.dispatch_method(
        *predicates,
        get_key_lookup=get_key_lookup,
        first_invocation_hook=first_invocation_hook,
        **kw,
    )


dispatch_method.__doc__ = reg.dispatch_method.__doc__


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

    parent: App | None = None
    """The parent in which this app was mounted."""

    request_class: type[Request[Self]] = Request
    """The class of the Request to create. Must be a subclass of
    :class:`morepath.Request`.

    By default the request class is :class:`morepath.Request`
    """

    logger_name = "morepath.directive"
    """Prefix used by dectate to log configuration actions.
    """

    setting = directive(action.SettingAction)
    setting_section = directive(action.SettingSectionAction)
    predicate_fallback = directive(action.PredicateFallbackAction)
    predicate = directive(action.PredicateAction)
    method = directive(action.MethodAction)
    converter = directive(action.ConverterAction)
    _path = directive(action.PathAction)
    path = directive(action.PathCompositeAction)
    permission_rule = directive(action.PermissionRuleAction)
    template_directory = directive(action.TemplateDirectoryAction)
    template_loader = directive(action.TemplateLoaderAction)
    template_render = directive(action.TemplateRenderAction)
    view = directive(action.ViewAction)
    json = directive(action.JsonAction)
    html = directive(action.HtmlAction)
    mount = directive(action.MountAction)
    defer_links = directive(action.DeferLinksAction)
    defer_class_links = directive(action.DeferClassLinksAction)
    tween_factory = directive(action.TweenFactoryAction)
    identity_policy = directive(action.IdentityPolicyAction)
    verify_identity = directive(action.VerifyIdentityAction)
    dump_json = directive(action.DumpJsonAction)
    link_prefix = directive(action.LinkPrefixAction)

    def __init__(self) -> None:
        pass

    def request(self, environ: WSGIEnvironment) -> Request[Self]:
        """Create a :class:`Request` given WSGI environment for this app.

        :param environ: WSGI environment
        :return: :class:`morepath.Request` instance
        """
        return self.request_class(environ, self)

    def __call__(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> Iterable[bytes]:
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
    def publish(self) -> Callable[[AnyRequest], BaseResponse]:
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
        # the last chance we have to commit the app is here, the
        # lookup may not be touched yet at this point
        if not self.is_committed():
            self.commit()

        registry: TweenRegistry = self.config.tween_registry
        return registry.wrap(self)

    def ancestors(self) -> Iterator[App]:
        """Return iterable of all ancestors of this app.

        Includes this app itself as the first ancestor, all the way
        up to the root app in the mount chain.
        """
        app: App | None = self
        while app is not None:
            yield app
            app = app.parent

    @reify
    def root(self) -> App:
        """The root application."""
        return list(self.ancestors())[-1]

    @overload
    def child(self, app: type[_AppT], **variables: Any) -> _AppT | None: ...
    @overload
    def child(self, app: _AppT) -> _AppT | None: ...
    @overload
    def child(self, app: str, **variables: Any) -> App | None: ...

    def child(self, app: type[App] | App | str, **variables: Any) -> App | None:
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
            if isinstance(app, str):
                factory = self.config.path_registry.named_mounted.get(app)
            else:
                factory = self.config.path_registry.mounted.get(app)
            if factory is None:
                return None
            result = factory(**variables)
        result.parent = self
        return result

    @overload
    def sibling(self, app: _AppT) -> _AppT | None: ...
    @overload
    def sibling(self, app: type[_AppT], **variables: Any) -> _AppT | None: ...
    @overload
    def sibling(self, app: str, **variables: Any) -> App | None: ...

    def sibling(
        self, app: type[App] | App | str, **variables: Any
    ) -> App | None:
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
    def settings(self) -> SettingRegistry:
        """Returns the settings bound to this app."""
        return self.config.setting_registry  # type: ignore[no-any-return]

    @classmethod
    def mounted_app_classes(
        cls, callback: Callable[..., object] | None = None
    ) -> set[type[App]]:
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
        discovery: set[type[App]] = set()
        found = {cls}
        while found:
            discovery.update(found)
            if callback is not None:
                callback(*found)
            found = {
                c for a in found for c in a.config.path_registry.mounted
            } - discovery
        return discovery

    @classmethod
    def commit(cls) -> set[type[App]]:
        """Commit the app, and recursively, the apps mounted under it.

        Mounted apps are discovered in breadth-first order.

        :return: the set of discovered app clasess.
        """
        return cls.mounted_app_classes(dectate.commit)

    @classmethod
    def init_settings(
        cls, settings: SupportsItems[str, SupportsItems[str, Any]]
    ) -> None:
        """Pre-fill the settings before the app is started.

        Add settings to App, which can act as normal, can be overridden, etc.

        :param settings: a dictionary of setting sections which contain
          dictionaries of settings.
        """

        def set_setting_section(
            section: str, section_settings: SupportsItems[str, Any]
        ) -> None:
            cls.setting_section(section)(lambda: section_settings)

        for section, section_settings in settings.items():
            set_setting_section(section, section_settings)

    @dispatch_method()
    def get_view(self, obj: Any, request: Request) -> BaseResponse:
        """Get the view that represents the obj in the context of a request.

        This view is a representation of the obj that can be rendered to a
        response. It may also return a :class:`morepath.Response`
        directly.

        Predicates are installed in :mod:`morepath.core` that inspect both
        ``obj`` and ``request`` to see whether a matching view can be found.

        You can also install additional predicates using the
        :meth:`morepath.App.predicate` and
        :meth:`morepath.App.precicate_fallback` directives.

        :param obj: model object to represent with view.
        :param request: :class:`morepath.Request` instance.
        :return: :class:`morepath.Response` object, or
          :class:`webob.exc.HTTPNotFound` if view cannot be found.
        """
        return HTTPNotFound()

    @dispatch_method("identity")
    def _verify_identity(self, identity: Identity) -> bool:
        """Returns True if the claimed identity can be verified.

        Look in the database to verify the identity, or in case of auth
        tokens, always consider known identities to be correct.

        :param: :class:`morepath.Identity` instance.
        :return: ``True`` if identity can be verified. By default no identity
        can be verified so this returns ``False``.
        """
        return False

    @dispatch_method("identity", "obj", reg.match_class("permission"))
    def _permits(
        self, identity: Identity | NoIdentity, obj: Any, permission: Any
    ) -> bool:
        """Returns ``True`` if identity has permission for model object.

        identity can be the special :data:`morepath.NO_IDENTITY`
        singleton; register for :class:`morepath.NoIdentity` to handle
        this case separately.

        :param identity: :class:`morepath.Identity`
        :param obj: model object
        :param permission: permission class.
        :return: ``True`` if identity has permission for obj.
        """
        return False

    @dispatch_method("obj")
    def _dump_json(self, obj: Any, request: AnyRequest) -> Any:
        """Dump an object as JSON.

        ``obj`` is any Python object, try to interpret it as JSON.

        :param obj: any Python object to convert to JSON.
        :param request: :class:`morepath.Request`
        :return: JSON representation (in Python form).
        """
        return obj

    def _link_prefix(self, request: AnyRequest) -> str:
        """Returns a prefix that's added to every link generated by request.

        By default :attr:`webob.request.BaseRequest.application_url` is used.

        :param request: :class:`morepath.Request`
        :return: prefix string to add before links.
        """
        return request.application_url  # type: ignore[no-any-return]

    @dispatch_method(reg.match_class("model"))
    def _class_path(
        self, model: type[Any], variables: dict[str, Any]
    ) -> PathInfo | None:
        """Get the path for a model class.

        :param model: model class or :class:`morepath.App` subclass.
        :param variables: dictionary with variables to reconstruct
        the path and URL parameters from path pattern.
        :return: a :class:`morepath.path.PathInfo` with path within this app,
          or ``None`` if the path couldn't be determined.
        """
        return None

    @dispatch_method("obj")
    def _path_variables(self, obj: Any) -> dict[str, Any] | None:
        """Get variables to use in path generation.

        :param obj: model object or :class:`morepath.App` instance.
        :return: a dict with the variables to use for constructing the path,
        or ``None`` if no such dict can be found.
        """
        return self._default_path_variables(obj)

    @dispatch_method("obj")
    def _default_path_variables(self, obj: Any) -> dict[str, Any] | None:
        """Get default variables to use in path generation.

        Invoked if no specific ``path_variables`` is registered.

        :param obj: model object for ::class:`morepath.App` instance.
        :return: a dict with the variables to use for constructing the
        path, or ``None`` if no such dict can be found.
        """
        return None

    @dispatch_method("obj")
    def _deferred_link_app(self, obj: Any) -> App | None:
        """Get application used for link generation.

        :param obj: model object to link to.
        :return: instance of :class:`morepath.App` subclass that handles
        link generation for this model, or ``None`` if no app exists
        that can construct link.
        """
        return None

    @dispatch_method(reg.match_class("model"))
    def _deferred_class_link_app(
        self, model: type[Any], variables: dict[str, Any] | None
    ) -> App | None:
        """Get application used for link generation for a model class.

        :param model: model class
        :param variables: dict of variables used to construct class link
        :return: instance of :class:`morepath.App` subclass that handles
        link generation for this model class, or ``None`` if no app exists
        that can construct link.
        """
        return None

    @classmethod
    def clean(cls) -> None:
        reg.clean_dispatch_methods(cls)

    def _identify(self, request: AnyRequest) -> Identity | NoIdentity | None:
        """Determine identity for request.

        :param request: a :class:`morepath.Request` instance.
        :return: a :class:`morepath.Identity` instance or ``None`` if
        no identity can be found. Can also return :data:`morepath.NO_IDENTITY`,
        but ``None`` is converted automatically to this.
        """
        return None

    def remember_identity(
        self, response: BaseResponse, request: AnyRequest, identity: Identity
    ) -> None:
        """Modify response so that identity is remembered by client.

        :param response: :class:`morepath.Response` to remember identity on.
        :param request: :class:`morepath.Request`
        :param identity: :class:`morepath.Identity`
        """
        pass

    def forget_identity(
        self, response: BaseResponse, request: AnyRequest
    ) -> None:
        """Modify response so that identity is forgotten by client.

        :param response: :class:`morepath.Response` to forget identity on.
        :param request: :class:`morepath.Request`
        """
        pass

    def _get_path(self, obj: Any) -> PathInfo | None:
        """Path for a model obj.

        Only includes path within the current app, does not take
        mounting into account.

        :param obj: model object
        :return: a :class:`morepath.path.PathInfo` with path within this app.
        """
        return self._class_path(
            obj.__class__,
            # NOTE: Path.__call__ will emit a LinkError if we got `None` back
            #       for _path_variables, so we technically don't need to do to
            #       anything here. It still might be worth to duplicate the
            #       check and error generation to here, so it's a little bit
            #       higher in the call stack.
            self._path_variables(obj),  # type: ignore[arg-type]
        )

    def _get_mounted_path(self, obj: Any) -> PathInfo | None:
        """Path for model obj including mounted path.

        Includes path to this app itself, so takes mounting into account.

        :param obj: model object (or :class:`morepath.App` instance).
        :return: a :class:`morepath.path.PathInfo` with fully resolved
          path in mounts.
        """
        paths = []
        parameters = {}
        app: App | None = self
        while app is not None:
            info = app._get_path(obj)
            if info is None:
                return None
            paths.append(info.path)
            parameters.update(info.parameters)
            obj = app
            app = app.parent
        paths.reverse()
        return PathInfo("/".join(paths).strip("/"), parameters)

    def _get_mounted_class_path(
        self, model: type[Any], variables: dict[str, Any]
    ) -> PathInfo | None:
        """Path for model class and variables including mounted path.

        Includes path to this app itself, so takes mounting into account.

        :param model: model class
        :param variables: dict with variables to use in the path
        :return: a :class:`morepath.path.PathInfo` with fully resolved
          path in mounts.
        """
        info = self._class_path(model, variables)
        if info is None:
            return None
        if self.parent is None:
            return info
        mount_info = self.parent._get_mounted_path(self)
        # FIXME: Can mount_info be None if we got here? If so
        #        what is the correct result?
        assert mount_info is not None
        path = mount_info.path
        if info.path:
            path += "/" + info.path
        parameters = info.parameters.copy()
        parameters.update(mount_info.parameters)
        return PathInfo(path, parameters)

    def _get_deferred_mounted_path(
        self, obj: Any
    ) -> tuple[PathInfo | None, App | None]:
        """Path for obj taking into account deferring apps.

        Like :meth:`morepath.App._get_mounted_path` but takes
        :meth:`morepath.App.defer_links` and
        :meth:`morepath.App.defer_class_links` directives into
        account.
        """

        def find(app: App, obj: Any) -> PathInfo | None:
            return app._get_mounted_path(obj)

        return self._follow_defers(find, obj)

    def _get_deferred_mounted_class_path(
        self, model: type[Any], variables: dict[str, Any]
    ) -> PathInfo | None:
        """Path for model and variables taking into account deferring apps.

        Like :meth:`morepath.App._get_mounted_class_path` but takes
        :meth:`morepath.App.defer_class_links` directive into
        account.
        """

        def find(
            app: App, model: type[Any], variables: dict[str, Any]
        ) -> PathInfo | None:
            return app._get_mounted_class_path(model, variables)

        info, app = self._follow_class_defers(find, model, variables)
        return info

    def _follow_defers(
        self, find: Callable[[App, Any], _T | None], obj: Any
    ) -> tuple[_T | None, App | None]:
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
        app: App | None = self
        while app is not None:
            if app in seen:
                raise LinkError("Circular defer. Cannot link to: %r" % obj)
            result = find(app, obj)
            if result is not None:
                return result, app
            seen.add(app)
            next_app = app._deferred_link_app(obj)
            if next_app is None:
                # only if we can establish the variables of the app here
                # fall back on using class link app
                variables = app._path_variables(obj)
                if variables is not None:
                    next_app = app._deferred_class_link_app(
                        obj.__class__, variables
                    )
            app = next_app
        return None, app

    def _follow_class_defers(
        self,
        find: Callable[[App, type[Any], dict[str, Any]], _T | None],
        model: type[Any],
        variables: dict[str, Any],
    ) -> tuple[_T | None, App | None]:
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
        app: App | None = self
        while app is not None:
            if app in seen:
                raise LinkError("Circular defer. Cannot link to: %r" % model)
            result = find(app, model, variables)
            if result is not None:
                return result, app
            seen.add(app)
            app = app._deferred_class_link_app(model, variables)
        return None, app
