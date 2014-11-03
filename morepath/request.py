from morepath import generic
from webob import BaseRequest, Response as BaseResponse
from .reify import reify
from .traject import parse_path
from .error import LinkError

try:
    from urllib.parse import urlencode
except ImportError:
    # Python 2
    from urllib import urlencode
import reg


NO_DEFAULT = reg.Sentinel('NO_DEFAULT')

SAME_APP = reg.Sentinel('SAME_APP')


class Request(BaseRequest):
    """Request.

    Extends :class:`webob.request.BaseRequest`
    """
    app = None
    """The :class:`App` object being handled by this request."""

    lookup = None
    """The :class:`reg.Lookup` object handling generic function calls."""

    def __init__(self, environ, app):
        super(Request, self).__init__(environ)
        self.app = app
        self.lookup = app.lookup
        self.unconsumed = parse_path(self.path_info)
        self._after = []

    @reify
    def body_obj(self):
        if not self.body:
            return None
        if self.content_type != 'application/json':
            return None
        return generic.load_json(self, self.json, lookup=self.lookup)

    @reify
    def identity(self):
        """Self-proclaimed identity of the user.

        The identity is established using the identity policy. Normally
        this would be an instance of :class:`morepath.security.Identity`.

        If no identity is claimed or established, or if the identity
        is not verified by the application, the identity is the the
        special value :attr:`morepath.security.NO_IDENTITY`.

        The identity can be used for authentication/authorization of
        the user, using Morepath permission directives.
        """
        # XXX annoying circular dependency
        from .security import NO_IDENTITY
        result = generic.identify(self, lookup=self.lookup,
                                  default=NO_IDENTITY)
        if result is NO_IDENTITY:
            return result
        if not generic.verify_identity(result, lookup=self.lookup):
            return NO_IDENTITY
        return result

    def view(self, obj, default=None, app=SAME_APP, **predicates):
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

        def find(app, obj):
            return generic.view.component(self, obj, lookup=app.lookup,
                                          default=None,
                                          predicates=predicates)

        view = _follow_defers(find, app, obj)
        if view is None:
            return default

        old_app = self.app
        app.set_implicit()
        self.app = app
        result = view(self, obj)
        old_app.set_implicit()
        self.app = old_app
        return result

    def link(self, obj, name='', default=None, app=SAME_APP):
        """Create a link (URL) to a view on a model instance.

        If no link can be constructed for the model instance, a
        :exc:``morepath.LinkError`` is raised. ``None`` is treated
        specially: if ``None`` is passed in the default value is
        returned.

        :param obj: the model instance to link to, or ``None``.
        :param name: the name of the view to link to. If omitted, the
          the default view is looked up.
        :param default: if ``None`` is passed in, the default value is
          returned. By default this is ``None``.
        :param app: If set, change the application to which the
          link is made. By default the link is made to an object
          in the current application. The ``defer_links`` directive
          can be used to change the default app for all instances of a
          particular class (if this app doesn't handle them).
        """
        if obj is None:
            return default

        if app is None:
            raise LinkError("Cannot link: app is None")

        if app is SAME_APP:
            app = self.app

        def find(app, obj):
            return generic.link(self, obj, app, lookup=app.lookup)

        info = _follow_defers(find, app, obj)

        if info is None:
            raise LinkError("Cannot link to: %r" % obj)

        path, parameters = info
        parts = []
        if path:
            parts.append(path)
        if name:
            parts.append(name)
        result = '/' + '/'.join(parts)
        if parameters:
            result += '?' + urlencode(parameters, True)
        return result

    def after(self, func):

        """Call function with response after this request is done.

        Can be used explicitly::

          def myfunc(response):
              response.headers.add('blah', 'something')
          request.after(my_func)

        or as a decorator::

          @request.after
          def myfunc(response):
              response.headers.add('blah', 'something')

        :param func: callable that is called with response
        :returns: func argument, not wrapped
        """
        self._after.append(func)
        return func

    def run_after(self, response):
        for after in self._after:
            after(response)


class Response(BaseResponse):
    """Response.

    Extends :class:`webob.response.Response`.
    """


def _follow_defers(find, app, obj):
    seen = set()
    while app is not None:
        if app in seen:
            raise LinkError("Circular defer. Cannot link to: %r" % obj)
        result = find(app, obj)
        if result is not None:
            return result
        seen.add(app)
        app = generic.deferred_link_app(app, obj, lookup=app.lookup)
    return None
