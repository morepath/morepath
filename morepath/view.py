import os
from . import generic
from .request import Response
import json
from webob.exc import HTTPFound, HTTPNotFound, HTTPForbidden
from webob import Response as BaseResponse


class TemplateEngineRegistry(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self._template_engines = {}
        self._template_files = {}

    def register_template_engine(self, extension, func):
        self._template_engines[extension] = func

    def register_template_file(self, name, base_path, func):
        self._template_files[name] = base_path, func

    def has_template_file(self, name):
        return self._template_files.get(name) is not None

    def get_template_file(self, name, request):
        info = self._template_files.get(name)
        if info is None:
            raise TemplateFileError(
                "Cannot find template_file for %s" % name)
        base_path, func = info
        return os.path.join(base_path, func(request))

    def get_template_render(self, name, original_render, module):
        _, extension = os.path.splitext(name)
        engine = self._template_engines.get(extension)
        if module is not None:
            search_path = os.path.dirname(module.__file__)
        else:
            # only in testing scenarios
            search_path = '/'
        return engine(name, original_render, self, search_path)


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


def register_view(registry, key_dict, view,
                  render=render_view,
                  template=None,
                  module=None,
                  permission=None,
                  internal=False):
    if template is not None:
        render = registry.get_template_render(template, render, module)
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
