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
        self.mounts = []
        self._after = []

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
        if not generic.verify_identity(result, lookup=self.lookup):
            return NO_IDENTITY
        return result

    @reify
    def mounted(self):
        return self.mounts[-1]

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
        return generic.linkmaker(self, self.mounted, lookup=self.lookup).view(
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
        return generic.linkmaker(self, self.mounted,
                                 lookup=self.lookup).link(obj, name, default)

    @reify
    def parent(self):
        """Obj to call :meth:`Request.link` or :meth:`Request.view` on parent.

        Get an object that represents the parent app that this app is mounted
        inside. You can call ``link`` and ``view`` on it.
        """
        return generic.linkmaker(self, self.mounted.parent, lookup=self.lookup)

    def child(self, app, **variables):
        """Obj to call :meth:`Request.link` or :meth:`Request.view` on child.

        Get an object that represents the application mounted in this app.
        You can call ``link`` and ``view`` on it.
        """
        return generic.linkmaker(self, self.mounted.child(app, **variables),
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
    def __init__(self, request, mounted):
        self.request = request
        self.mounted = mounted

    def link(self, obj, name='', default=None):
        if obj is None:
            return default
        path, parameters = generic.link(
            self.request, obj, self.mounted, lookup=self.mounted.lookup)
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
            self.request, obj, lookup=self.mounted.lookup, default=default,
            predicates=predicates)
        if view is None:
            return None
        return view(self.request, obj)

    @reify
    def parent(self):
        return generic.linkmaker(self.request, self.mounted.parent,
                                 lookup=self.mounted.lookup)

    def child(self, app, **variables):
        return generic.linkmaker(self.request,
                                 self.mounted.child(app, **variables),
                                 lookup=self.mounted.lookup)


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

    def child(self, app, **variables):
        return NothingMountedLinkMaker(self.request)
