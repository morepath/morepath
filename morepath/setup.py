from .app import global_app
from .config import Config
import morepath.directive
from morepath import generic
from .error import LinkError
from .app import App
from .request import Request, Response
from werkzeug.wrappers import BaseResponse
from .traject import traject_consumer
import morepath
from reg import Lookup

assert morepath.directive  # we need to make the function directive work


def setup():
    config = Config()
    config.scan(morepath, ignore=['.tests'])
    config.commit()
    # should use a configuration directive for this
    global_app.register(generic.consumer, [object], traject_consumer)


@global_app.function(generic.path, object)
def app_path(model, lookup):
    result = []
    while True:
        base = generic.base(model, lookup=lookup, default=None)
        if base is None:
            break
        traject = generic.traject(base, lookup=lookup)
        result.append(traject.path(model))
        model = base
    result.reverse()
    return '/'.join(result)


@global_app.function(generic.traject, App)
def app_traject(app):
    return app.traject


@global_app.function(generic.link, Request, object)
def link(request, model):
    lookup = request.lookup
    result = []
    mounts = request.mounts[:]
    while True:
        result.append(app_path(model, lookup=lookup))
        mount = mounts.pop()
        if not mounts:
            break
        model = mount
        lookup = mount.app.lookup
    result.reverse()
    return '/'.join(result)


@global_app.function(generic.lookup, App)
def app_lookup(model):
    return model.lookup()


@global_app.function(generic.response, Request, object)
def get_response(request, model):
    view = generic.view.component(
        request, model, lookup=request.lookup,
        default=None)
    if view is None:
        return None
    content = view(request, model)
    if isinstance(content, BaseResponse):
        # the view took full control over the response
        return content
    # XXX consider always setting a default render so that view.render
    # can never be None
    if view.render is not None:
        response = view.render(content)
    else:
        response = Response(content)
    return response
