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


class Request(BaseRequest):
    """Request.

    Extends :class:`webob.request.BaseRequest`
    """
    def __init__(self, environ):
        super(Request, self).__init__(environ)
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

    def view(self, obj, default=None, **predicates):
        """Call view for model instance.

        This does not render the view, but calls the appropriate
        view function and returns its result.

        :param obj: the model instance to call the view on.
        :param default: default value if view is not found.
        :param predicates: extra predicates to modify view
          lookup, such as ``name`` and ``request_method``. The default
          ``name`` is empty, so the default view is looked up,
          and the default ``request_method`` is ``GET``. If you introduce
          your own predicates you can specify your own default.
        """
        return generic.linkmaker(self, self.app, lookup=self.lookup).view(
            obj, default, **predicates)

    def link(self, obj, name='', default=None):
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

        """
        return generic.linkmaker(self, self.app,
                                 lookup=self.lookup).link(obj, name, default)

    @reify
    def parent(self):
        """Obj to call :meth:`Request.link` or :meth:`Request.view` on parent.

        Get an object that represents the parent app that this app is mounted
        inside. You can call ``link`` and ``view`` on it.
        """
        return generic.linkmaker(self, self.app.parent, lookup=self.lookup)

    def child(self, app, **context):
        """Obj to call :meth:`Request.link` or :meth:`Request.view` on child.

        Get an object that represents the application mounted in this app.
        You can call ``link`` and ``view`` on it.

        :param app: either subclass of :class:`morepath.App` that you
          want to link to, or a string. This string represents the
          name of the mount (by default it's the path under which the mount
          happened).
        :param ``**context``: Keyword parameters. These are the
          arguments with which the app was instantiated when mounted.
        """
        return generic.linkmaker(self, self.app.child(app, **context),
                                 lookup=self.lookup)

    def sibling(self, app, **context):
        """Obj to call :meth:`Request.link` or :meth:`Request.view` on sibling.

        Get an object that represents the application mounted as a
        sibling to this app, so the child of the parent. You can call
        ``link`` and ``view`` on it.

        :param app: either subclass of :class:`morepath.App` that you
          want to link to, or a string. This string represents the
          name of the mount (by default it's the path under which the mount
          happened).
        :param ``**context``: Keyword parameters. These are the
          arguments with which the app was instantiated when mounted.
        """
        if self.app.parent is None:
            return NothingMountedLinkMaker(self)
        return generic.linkmaker(self, self.app.parent.child(app,
                                                             **context),
                                 lookup=self.lookup)

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


class LinkMaker(object):
    def __init__(self, request, app):
        self.request = request
        self.app = app

    def link(self, obj, name='', default=None):
        if obj is None:
            return default
        path, parameters = generic.link(
            self.request, obj, self.app, lookup=self.app.lookup)
        parts = []
        if path:
            parts.append(path)
        if name:
            parts.append(name)
        result = '/' + '/'.join(parts)
        if parameters:
            result += '?' + urlencode(parameters, True)
        return result

    def view(self, obj, default=None, **predicates):
        view = generic.view.component(
            self.request, obj, lookup=self.app.lookup, default=default,
            predicates=predicates)
        if view is None:
            return None
        old_app = self.request.app
        self.app.set_implicit()
        self.request.app = self.app
        result = view(self.request, obj)
        old_app.set_implicit()
        self.request.app = old_app
        return result

    @reify
    def parent(self):
        return generic.linkmaker(self.request, self.app.parent,
                                 lookup=self.app.lookup)

    def child(self, app, **context):
        return generic.linkmaker(self.request,
                                 self.app.child(app, **context),
                                 lookup=self.app.lookup)


class NothingMountedLinkMaker(object):
    def __init__(self, request):
        self.request = request

    def link(self, obj, name='', default=None):
        raise LinkError("Cannot link to %r (name %r)" % (obj, name))

    def view(self, obj, default=None, **predicates):
        raise LinkError("Cannot view %r (predicates %r)" % (obj, predicates))

    @reify
    def parent(self):
        return NothingMountedLinkMaker(self.request)

    def child(self, app, **context):
        return NothingMountedLinkMaker(self.request)
