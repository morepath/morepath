"""Morepath request implementation.

Entirely documented in :class:`morepath.Request` and
:class:`morepath.Response` in the public API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, cast, overload

from webob import Response as BaseResponse
from webob.request import BaseRequest

from dectate import Sentinel

from .authentication import NO_IDENTITY
from .error import LinkError
from .reify import reify
from .traject import create_path, parse_path

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing_extensions import TypeVar

    from dectate import CodeInfo

    from .app import App
    from .authentication import Identity, NoIdentity
    from .types import WSGIEnvironment
    from .view import View

    _AppT = TypeVar("_AppT", bound="App", default="App", covariant=True)
else:
    from typing import TypeVar

    _AppT = TypeVar("_AppT", bound="App", covariant=True)


_T = TypeVar("_T")
# NOTE: Technically `webob.Response` is the correct bound, since we're not
#       guaranteed to always get a `morepath.Response`, but considering
#       that `morepath.Response` does not add any attributes of its own,
#       the improved ergonomics of being able to annotate as either
#       `webob.Response` or `morepath.Response` interchangeably outweigh
#       the risks of `morepath.Response` being inaccurate in some
#       cirumstances.
_AfterT = TypeVar("_AfterT", bound="Callable[[Response], object]")

SAME_APP: Sentinel = Sentinel("SAME_APP")


class Request(BaseRequest, Generic[_AppT]):
    """Request.

    Extends :class:`webob.request.BaseRequest`
    """

    app: _AppT
    path_code_info: CodeInfo | None = None
    view_code_info: CodeInfo | None = None
    view_name: str | None = None

    def __init__(self, environ: WSGIEnvironment, app: _AppT, **kw: Any) -> None:
        super().__init__(environ, **kw)
        # parse path, normalizing dots away in
        # in case the client didn't do the normalization
        path_info = self.path_info
        segments = parse_path(path_info)
        # optimization: only if the normalized path is different from the
        # original path do we set it to the webob request, as this is
        # relatively expensive. Webob updates the environ as well
        new_path_info = create_path(segments)
        if new_path_info != path_info:
            self.path_info = new_path_info
        # reverse to get unconsumed
        segments.reverse()
        self.unconsumed = segments
        """Stack of path segments that have not yet been consumed.

        See :mod:`morepath.publish`.
        """

        self._root_app = app

        self.app = app
        """:class:`morepath.App` instance currently handling request.
        """
        self._after: list[Callable[[BaseResponse], object]] = []
        self._link_prefix_cache: dict[type[object], str] = {}

    def reset(self) -> None:
        """Reset request.

        This resets the request back to the state it had when request
        processing started. This is used by ``more.transaction`` when it
        retries a transaction.
        """
        self.make_body_seekable()
        segments = parse_path(self.path_info)
        segments.reverse()
        self.unconsumed = segments
        self.app = self._root_app
        self._after = []

    @reify
    def identity(self) -> Identity | NoIdentity:
        """Self-proclaimed identity of the user.

        The identity is established using the identity policy. Normally
        this would be an instance of :class:`morepath.Identity`.

        If no identity is claimed or established, or if the identity
        is not verified by the application, the identity is the the
        special value :attr:`morepath.NO_IDENTITY`.

        The identity can be used for authentication/authorization of
        the user, using Morepath permission directives.
        """
        result = self.app._identify(self)
        if result is None or result is NO_IDENTITY:
            return NO_IDENTITY

        result = cast("Identity", result)
        if not self.app._verify_identity(result):
            return NO_IDENTITY
        return result

    def link_prefix(self, app: App | None = None) -> str:
        """Prefix to all links created by this request.

        :param app: Optionally use the given app to create the link.
            This leads to use of the link prefix configured for the given app.
            This parameter is mainly used internally for link creation.

        """
        app = app or self.app

        cached = self._link_prefix_cache.get(app.__class__)
        if cached is not None:
            return cached

        prefix = self._link_prefix_cache[app.__class__] = app._link_prefix(self)

        return prefix

    def view(
        self,
        obj: object,
        default: _T | None = None,
        app: App | Sentinel = SAME_APP,
        **predicates: Any,
    ) -> Any | _T | None:
        """Call view for model instance.

        This does not render the view, but calls the appropriate
        view function and returns its result.

        :param obj: the model instance to call the view on.
        :param default: default value if view is not found.
        :param app: If set, change the application in which to look up
          the view. By default the view is looked up for the current
          application. The ``defer_links`` directive can be used to change
          the default app for all instances of a particular class.
        :param predicates: extra predicates to modify view
          lookup, such as ``name`` and ``request_method``. The default
          ``name`` is empty, so the default view is looked up,
          and the default ``request_method`` is ``GET``. If you introduce
          your own predicates you can specify your own default.
        """
        if app is None:
            raise LinkError("Cannot view: app is None")

        if app is SAME_APP:
            app = self.app

        assert not isinstance(app, Sentinel)
        predicates["model"] = obj.__class__

        def find(app: App, obj: object) -> View | None:
            # NOTE: The fact that this is always a view instance is very much an
            #       implementation detail and relies on all views getting registered
            #       by the view action, rather than manually through get_view.register
            return cast(
                "View | None",
                app.get_view.by_predicates(**predicates).component,
            )

        view, found_app = app._follow_defers(find, obj)
        if view is None:
            return default

        assert found_app is not None
        old_app = self.app
        self.app = found_app  # type: ignore[assignment]
        # need to use value as view is registered as a function, not
        # as a wrapped method
        try:
            result = view.func(obj, self)
        finally:
            # Make sure we always restore the original bound app, even
            # if the view throws an exception
            self.app = old_app
        return result

    @overload
    def link(  # pyright: ignore[reportOverlappingOverload]
        self,
        obj: None,
        name: str = "",
        default: None = None,
        app: App | Sentinel = ...,
    ) -> None: ...
    @overload
    def link(
        self, obj: None, name: str, default: _T, app: App | Sentinel = ...
    ) -> _T: ...
    @overload
    def link(
        self,
        obj: object,
        name: str = "",
        default: Any = None,
        app: App | Sentinel = ...,
    ) -> str: ...

    def link(
        self,
        obj: object,
        name: str = "",
        default: Any = None,
        app: App | Sentinel = SAME_APP,
    ) -> Any | None:
        """Create a link (URL) to a view on a model instance.

        The resulting link is prefixed by the link prefix. By default
        this is the full URL based on the Host header.

        You can configure the link prefix for an application using the
        :meth:`morepath.App.link_prefix` directive.

        If no link can be constructed for the model instance, a
        :exc:`morepath.error.LinkError` is raised. ``None`` is treated
        specially: if ``None`` is passed in the default value is
        returned.

        The :meth:`morepath.App.defer_links` or
        :meth:`morepath.App.defer_class_links` directives can be used
        to defer link generation for all instances of a particular
        class (if this app doesn't handle them) to another app.

        :param obj: the model instance to link to, or ``None``.
        :param name: the name of the view to link to. If omitted, the
          the default view is looked up.
        :param default: if ``None`` is passed in, the default value is
          returned. By default this is ``None``.
        :param app: If set, change the application to which the
          link is made. By default the link is made to an object
          in the current application.

        """
        if obj is None:
            return default

        if app is None:
            raise LinkError("Cannot link: app is None")

        if app is SAME_APP:
            app = self.app

        assert not isinstance(app, Sentinel)
        info, found_app = app._get_deferred_mounted_path(obj)

        if info is None:
            raise LinkError("Cannot link to: %r" % obj)

        return info.url(self.link_prefix(found_app), name)

    def class_link(
        self,
        model: type,
        variables: dict[str, Any] | None = None,
        name: str = "",
        app: App | Sentinel = SAME_APP,
    ) -> str:
        """Create a link (URL) to a view on a class.

        Given a model class and a variables dictionary, create a link
        based on the path registered for the class and interpolate the
        variables.

        If you have an instance of the model available you'd link to the
        model instead, but in some cases it is expensive to instantiate
        the model just to create a link. In this case `class_link` can be
        used as an optimization.

        The :meth:`morepath.App.defer_class_links` directive can be
        used to defer link generation for a particular class (if this
        app doesn't handle them) to another app.

        Note that the :meth:`morepath.App.defer_links` directive has
        **no** effect on ``class_link``, as it needs an instance of the
        model to work, which is not available.

        If no link can be constructed for the model class, a
        :exc:`morepath.error.LinkError` is raised. This error is
        also raised if you don't supply enough variables. Additional
        variables not used in the path are interpreted as URL
        parameters.

        :param model: the model class to link to.
        :param variables: a dictionary with as keys the variable names,
          and as values the variable values. These are used to construct
          the link URL. If omitted, the dictionary is treated as containing
          no variables.
        :param name: the name of the view to link to. If omitted, the
          the default view is looked up.
        :param app: If set, change the application to which the
          link is made. By default the link is made to an object
          in the current application.

        """
        if variables is None:
            variables = {}

        if app is None:
            raise LinkError("Cannot link: app is None")

        if app is SAME_APP:
            app = self.app

        assert not isinstance(app, Sentinel)
        info = app._get_deferred_mounted_class_path(model, variables)

        if info is None:
            raise LinkError("Cannot link to class: %r" % model)

        return info.url(self.link_prefix(), name)

    def resolve_path(
        self, path: str, app: App | Sentinel = SAME_APP
    ) -> Any | None:
        """Resolve a path to a model instance.

        The resulting object is a model instance, or ``None`` if the
        path could not be resolved.

        :param path: URL path to resolve.
        :param app: If set, change the application in which the
          path is resolved. By default the path is resolved in the
          current application.
        :return: instance or ``None`` if no path could be resolved.
        """
        if app is None:
            raise LinkError("Cannot path: app is None")

        if app is SAME_APP:
            app = self.app

        assert not isinstance(app, Sentinel)
        request = Request(self.environ.copy(), app, path_info=path)
        # try to resolve imports..
        from .publish import resolve_model

        return resolve_model(request)

    def after(self, func: _AfterT) -> _AfterT:
        """Call a function with the response after a successful request.

        A request is considered *successful* if the HTTP status is a 2XX or a
        3XX code (e.g. 200 OK, 204 No Content, 302 Found).
        In this case ``after`` *is* called.

        A request is considered *unsuccessful* if the HTTP status lies outside
        the 2XX-3XX range (e.g. 403 Forbidden, 404 Not Found,
        500 Internal Server Error). Usually this happens if an exception
        occurs. In this case ``after`` is *not* called.

        Some exceptions indicate a successful request however and their
        occurrence still leads to a call to ``after``. These exceptions
        inherit from either :class:`webob.exc.HTTPOk` or
        :class:`webob.exc.HTTPRedirection`.

        You use `request.after` inside a view function definition.

        It can be used explicitly::

          @App.view(model=SomeModel)
          def some_model_default(self, request):
              def myfunc(response):
                  response.headers.add('blah', 'something')
              request.after(my_func)

        or as a decorator::

          @App.view(model=SomeModel)
          def some_model_default(self, request):
              @request.after
              def myfunc(response):
                  response.headers.add('blah', 'something')

        :param func: callable that is called with response
        :return: func argument, not wrapped
        """
        # NOTE: See the note on _AfterT
        self._after.append(func)  # type: ignore[arg-type]
        return func

    def _run_after(self, response: BaseResponse) -> None:
        """Run callbacks registered with :meth:`morepath.Request.after`."""
        # if we don't have anything to run, don't even check status
        if not self._after:
            return
        # run after only if it's not a 2XX or 3XX response
        if response.status[0] not in ("2", "3"):
            return
        for after in self._after:
            after(response)

    def clear_after(self) -> None:
        self._after = []


class Response(BaseResponse):
    """Response.

    Extends :class:`webob.response.Response`.
    """
