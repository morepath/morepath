"""Rendering views.

A view is a function that returns something. This can be a
:class:`morepath.Response`, but it can also be a structure (such a
dict) that should be rendered *to* a response. If the view is a JSON
view this dumps this structure as JSON. If the view is a HTML view
this structure can be converted to HTML using a template.

:func:`morepath.render_json`, :func:`morepath.render_html` and
:func:`morepath.redirect` are members of the public API.

"""

from webob.exc import HTTPFound, HTTPNotFound, HTTPForbidden
from webob import Response as BaseResponse

from .request import Response


class View:
    """A view as registered with :meth:`morepath.App.get_view`.

    :param func: view function. Given a model instance and a request
      argument, this function must return either a structure that can
      be turned into a response or a response.
    :param render: a function used to render view function return value
      as a response.
    :param load: a function used to load the body data into a third
      argument to the view.
    :param permission: permission class that the identity must have
      according to permission rules. If the view doesn't have the
      permission access is forbidden.
    :param internal: bool to indicate whether this view is internal.
      If the view is internal you can use it with
      :meth:`morepath.Request.view` but it doesn't have a URL
      and will be 404 Not Found.
    """

    def __init__(
        self,
        func,
        render=None,
        load=None,
        permission=None,
        internal=False,
        code_info=None,
    ):
        self.func = func
        self.render = render or render_view
        self.load = load
        self.permission = permission
        self.internal = internal
        self.code_info = code_info

    def __call__(self, app, obj, request):
        """Render a model instance.

        If view is internal it cannot be rendered.

        If the identity does not have the permission for
        this object according to the permission rules then
        :class:`webob.exc.HTTPForbidden` is raised.

        Any functions specified using :meth:`morepath.Request.after`
        are run against the response once it is created, if that
        response is not an error.

        :param obj: the model instance
        :param request: the request
        :return: A :class:`webob.response.Response` instance.
        """
        request.view_code_info = self.code_info
        if self.internal:
            raise HTTPNotFound()
        if self.permission is not None and not request.app._permits(
            request.identity, obj, self.permission
        ):
            raise HTTPForbidden()
        if self.load is not None:
            content = self.func(obj, request, self.load(request))
        else:
            content = self.func(obj, request)
        if isinstance(content, BaseResponse):
            # the view took full control over the response
            response = content
        else:
            response = self.render(content, request)

        request._run_after(response)

        return response


def render_view(content, request):
    """Default render function for view if none was supplied.

    This just assumes the content is a string and renders it into
    a response.

    :param content: content as returned by view function.
    :param request: request object
    :return: a response instance with the content.
    """
    return Response(content, content_type="text/plain")


def render_json(content, request):
    """Take dict/list/string/number content and return json response.

    This respects the :meth:`morepath.App.dump_json` directive that
    can be used to serialize any object to JSON. By default this
    serializes Python objects like dicts, strings to JSON.

    :param content: content as returned from view function.
    :param request: a :class:`morepath.Request` instance.
    :return: a :class:`morepath.Response` instance with a serialized
      JSON body.
    """
    return Response(
        json_body=request.app._dump_json(content, request),
        content_type="application/json",
    )


def render_html(content, request):
    """Take string and return text/html response.

    :param content: contnet as returned from view function.
    :param request: a :class:`morepath.Request` instance.
    :return: a :class:`morepath.Response` instance with ``content``
      as the body.
    """
    return Response(content, content_type="text/html")


def redirect(location):
    """Return a response object that redirects to location.

    :param location: a URL to redirect to.
    :return: a :class:`webob.exc.HTTPFound` response object. You can
      return this from a view to redirect.
    """
    return HTTPFound(location=location)
