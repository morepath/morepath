from . import generic
from .request import Response
import json
from webob.exc import HTTPFound


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


def register_view(registry, key_dict, view, render=None, permission=None,
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
    return HTTPFound(location=location)
