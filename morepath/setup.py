from .app import global_app
from .config import Config
import morepath.directive
from morepath import generic
from .error import LinkError
from .app import App
from .request import Request, Response
from .traject import traject_consumer
import morepath
from reg import Lookup

assert morepath.directive  # we need to make the component directive work


def setup():
    config = Config()
    config.scan(morepath, ignore=['.tests'])
    config.commit()
    # XXX could be registered with @component too
    global_app.register(generic.consumer, [object], traject_consumer)


@global_app.function(generic.path, [Request, object])
def traject_path(request, model):
    base = generic.base(model, lookup=request.lookup, default=None)
    if base is None:
        raise LinkError(
            "cannot determine model base for %r" % model)
    traject = generic.traject(base, lookup=request.lookup, default=None)
    if traject is None:
        raise LinkError(
            "cannot determine traject path info for base %r" % base)
    return traject.get_path(model)


@global_app.function(generic.traject, [App])
def app_traject(app):
    return app.traject


@global_app.function(generic.path, [Request, App])
def app_path(request, model):
    return model.name


@global_app.function(generic.base, [App])
def app_base(model):
    return model.parent


@global_app.function(generic.link, [Request, object])
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


@global_app.function(generic.lookup, [App])
def app_lookup(model):
    return Lookup(model.class_lookup())


@global_app.function(generic.response, [Request, object])
def get_response(request, model):
    resource = generic.resource.component(
        request, model, lookup=request.lookup,
        default=None)
    if resource is None:
        return None
    content = resource(request, model)
    response = None
    if isinstance(content, Response):
        response = content
    elif isinstance(content, basestring):
        response = Response(content)
    if resource.render is not None:
        if isinstance(content, Response):
            content = response.get_data(as_text=True)
        if response is None:
            response = Response()
        response = resource.render(response, content)
    assert response is not None, "Cannot render content: %r" % content
    return response
