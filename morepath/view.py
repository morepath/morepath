from . import generic
from .request import Response
import json
from webob.exc import HTTPFound, HTTPNotFound, HTTPForbidden
from webob import Response as BaseResponse


class View(object):
    def __init__(self, func, render, permission, internal):
        self.func = func
        self.render = render
        self.permission = permission
        self.internal = internal

    def __call__(self, request, model):
        # the argument order is reversed here for the actual view function
        # this still makes request weigh stronger in multiple dispatch,
        # but lets view authors write 'self, request'.
        return self.func(model, request)

    def response(self, request, obj):
        if self.internal:
            raise HTTPNotFound()
        if (self.permission is not None and
            not generic.permits(request.identity, obj, self.permission,
                                lookup=request.lookup)):
            raise HTTPForbidden()
        content = self(request, obj)
        if isinstance(content, BaseResponse):
            # the view took full control over the response
            return content
        response = self.render(content, request)
        request.run_after(response)
        return response


def render_view(content, request):
    """Default render function for view if none was supplied.
    """
    return Response(content, content_type='text/plain')


def register_view(registry, key_dict, view, render=render_view,
                  permission=None,
                  internal=False):
    v = View(view, render, permission, internal)
    registry.register_function(generic.view, v, **key_dict)


def render_json(content, request):
    """Take dict/list/string/number content and return json response.
    """
    return Response(json.dumps(generic.dump_json(request, content,
                                                 lookup=request.lookup)),
                    content_type='application/json')


def render_html(content, request):
    """Take string and return text/html response.
    """
    return Response(content, content_type='text/html')


def redirect(location):
    """Return a response object that redirects to location.
    """
    return HTTPFound(location=location)
