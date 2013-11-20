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


# XXX is request parameter needed?
@global_app.function(generic.path, Request, object)
def traject_path(request, model, lookup):
    base = generic.base(model, lookup=lookup, default=None)
    if base is None:
        raise LinkError(
            "cannot determine model base for %r" % model)
    traject = generic.traject(base, lookup=lookup, default=None)
    if traject is None:
        raise LinkError(
            "cannot determine traject path info for base %r" % base)
    return traject.path(model)


@global_app.function(generic.traject, App)
def app_traject(app):
    return app.traject


@global_app.function(generic.path, Request, App)
def app_path(request, model):
    return model.name


@global_app.function(generic.base, App)
def app_base(model):
    return model.parent


@global_app.function(generic.link, Request, object)
def link(request, model):
    result = []
    lookup = request.lookup
    while True:
        path = generic.path(request, model, lookup=lookup)
        if path:
            result.append(path)
        model = generic.base(model, lookup=lookup, default=None)
        if model is None:
            break
        # XXX should switch lookup back to lookup of base model in order
        # to mimic what happens during path resolution
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
