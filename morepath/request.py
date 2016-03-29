from webob import BaseRequest, Response as BaseResponse

from . import generic
from .reify import reify
from .traject import normalize_path, parse_path
from .error import LinkError


try:
    from urllib.parse import urlencode, quote
except ImportError:
    # Python 2
    from urllib import urlencode, quote
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

    def __init__(self, environ, app, **kw):

        environ['PATH_INFO'] = normalize_path(environ['PATH_INFO'])

        super(Request, self).__init__(environ, **kw)
        self.app = app
        self.lookup = app.lookup
        self.unconsumed = parse_path(self.path_info)
        self._after = []
        self._link_prefix_cache = {}

    @reify
    def body_obj(self):
        """JSON object, converted to an object.

        You can use the :meth:`App.load_json` directive to specify
        how to transform JSON to a Python object. By default, no
        conversion takes place, and ``body_obj`` is identical to
        the ``json`` attribute.
        """
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
        result = generic.identify(self, lookup=self.lookup)
        if result is None or result is NO_IDENTITY:
            return NO_IDENTITY
        if not generic.verify_identity(result, lookup=self.lookup):
            return NO_IDENTITY
        return result

    def link_prefix(self):
        """Prefix to all links created by this request."""
        cached = self._link_prefix_cache.get(self.app.__class__)
        if cached is not None:
            return cached

        prefix = self._link_prefix_cache[self.app.__class__]\
               = generic.link_prefix(self, lookup=self.lookup)

        return prefix

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

        predicates['model'] = obj.__class__

        def find(app, obj):
            return generic.view.component_key_dict(lookup=app.lookup,
                                                   **predicates)

        view, app = _follow_defers(find, app, obj)
        if view is None:
            return default

        old_app = self.app
        old_lookup = self.lookup
        app.set_implicit()
        self.app = app
        self.lookup = app.lookup
        result = view(self, obj)
        old_app.set_implicit()
        self.app = old_app
        self.lookup = old_lookup
        return result

    def link(self, obj, name='', default=None, app=SAME_APP):
        """Create a link (URL) to a view on a model instance.

        The resulting link is prefixed by the link prefix. By default
        this is the full URL based on the Host header.

        You can configure the link prefix for an application using the
        :meth:`morepath.App.link_prefix` directive.

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
            return link(obj, app)

        info, app = _follow_defers(find, app, obj)

        if info is None:
            raise LinkError("Cannot link to: %r" % obj)

        path, parameters = info
        return self._encode_link(path, name, parameters)

    def class_link(self, model, variables=None, name='', app=SAME_APP):
        """Create a link (URL) to a view on a class.

        Given a model class and a variables dictionary, create a link
        based on the path registered for the class and interpolate the
        variables.

        If you have an instance of the model available you'd link to the
        model instead, but in some cases it is expensive to instantiate
        the model just to create a link. In this case `class_link` can be
        used as an optimization.

        Note that the `defer_links` directive has no effect on `class_link`,
        as it needs an instance of the model to work, which is not
        available.

        If no link can be constructed for the model class, a
        :exc:``morepath.LinkError`` is raised. This error is also
        raised if you don't supply enough variables. Additional variables
        not used in the path are interpreted as URL parameters.

        :param model: the model class to link to.
        :param variables: a dictionary with as keys the variable names,
          and as values the variable values. These are used to construct
          the link URL. If omitted, the dictionary is treated as containing
          no variables.
        :param name: the name of the view to link to. If omitted, the
          the default view is looked up.
        :param app: If set, change the application to which the
          link is made. By default the link is made to an object
          in the current application. The ``defer_links`` directive has
          no effect.
        """
        if variables is None:
            variables = {}

        if app is None:
            raise LinkError("Cannot link: app is None")

        if app is SAME_APP:
            app = self.app

        info = class_link(model, variables, app)

        if info is None:
            raise LinkError("Cannot link to class: %r" % model)

        path, parameters = info

        return self._encode_link(path, name, parameters)

    def _encode_link(self, path, name, parameters):
        parts = []
        if path:
            parts.append(quote(path.encode('utf-8')))
        if name:
            parts.append(name)
        result = self.link_prefix() + '/' + '/'.join(parts)
        if parameters:
            parameters = dict((key, [v.encode('utf-8') for v in value])
                              for (key, value) in parameters.items())
            result += '?' + urlencode(parameters, True)
        return result

    def resolve_path(self, path, app=SAME_APP):
        """Resolve a path to a model instance.

        The resulting object is a model instance, or ``None`` if the
        path could not be resolved.

        :param path: URL path to resolve.
        :param app: If set, change the application in which the
          path is resolved. By default the path is resolved in the
          current application.
        :returns: instance or ``None`` if no path could be resolved.
        """
        if app is None:
            raise LinkError("Cannot path: app is None")

        if app is SAME_APP:
            app = self.app

        request = Request(self.environ.copy(), app, path_info=path)
        # try to resolve imports..
        from .publish import resolve_model
        return resolve_model(request)

    def after(self, func):
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
        :returns: func argument, not wrapped
        """
        self._after.append(func)
        return func

    def run_after(self, response):
        for after in self._after:
            after(response)

    def clear_after(self):
        self._after = []


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
            return result, app
        seen.add(app)
        app = generic.deferred_link_app(app, obj, lookup=app.lookup)
    return None, app


def link(obj, app):
    """Create a link (URL) to a model instance.

    Take mounted applications into account.
    """
    path_info = generic.path(obj, lookup=app.lookup)
    if path_info is None:
        return None
    path, parameters = path_info
    return mounted_link(path, parameters, app)


def class_link(model, variables, app):
    """Create a link to a model class given variables.

    Take mounted applications into account.
    """
    path_info = generic.class_path(model, variables=variables,
                                   lookup=app.lookup)
    if path_info is None:
        return None
    path, parameters = path_info
    return mounted_link(path, parameters, app)


def mounted_link(path, parameters, app):
    result = [path]
    obj = app
    app = app.parent
    while app is not None:
        path_info = generic.path(obj, lookup=app.lookup)
        if path_info is None:
            return None
        path, params = path_info
        result.append(path)
        parameters.update(params)
        obj = app
        app = app.parent
    result.reverse()
    return '/'.join(result).strip('/'), parameters
