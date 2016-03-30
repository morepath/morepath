import json
from webob.exc import HTTPFound, HTTPNotFound, HTTPForbidden
from webob import Response as BaseResponse

from . import generic
from .request import Response
from .app import RegRegistry
from .template import TemplateEngineRegistry


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
            response = content
        else:
            response = self.render(content, request)

        # run request after if it's a 2XX or 3XX response
        if 200 <= response.status_code <= 399:
            request.run_after(response)

        return response


def render_view(content, request):
    """Default render function for view if none was supplied.
    """
    return Response(content, content_type='text/plain')


class ViewRegistry(object):
    factory_arguments = {
        'reg_registry': RegRegistry,
        'template_engine_registry': TemplateEngineRegistry,
    }

    def __init__(self, reg_registry, template_engine_registry):
        self.reg_registry = reg_registry
        self.template_engine_registry = template_engine_registry

    def predicate_key(self, key_dict):
        return self.reg_registry.key_dict_to_predicate_key(
            generic.view.wrapped_func,
            key_dict)

    def register_view(self, key_dict, view,
                      render=render_view,
                      template=None,
                      permission=None,
                      internal=False):
        if template is not None:
            render = self.template_engine_registry.get_template_render(
                template, render)
        v = View(view, render, permission, internal)
        self.reg_registry.register_function(generic.view, v, **key_dict)


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
