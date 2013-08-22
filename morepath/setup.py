from .app import global_app
from .config import Config
import morepath.directive
from .interfaces import (IConsumer, ILookup, IModelBase, IRoot,
                         IPath, LinkError, IApp, IContent, IResponse,
                         IResourceRegistration)
from .request import Request
from .traject import traject_consumer
import morepath
from comparch import Lookup

assert morepath.directive  # we need to make the component directive work


def setup():
    config = Config()
    config.scan(morepath, ignore=['.tests'])
    config.commit()
    # XXX could be registered with @component too
    global_app.register(IConsumer, [IApp], traject_consumer)


@global_app.component(IPath, [Request, object])
def traject_path(request, model):
    base = IModelBase.adapt(model, lookup=request.lookup, default=None)
    traject = base.traject
    if traject is None:
        raise LinkError(
            "cannot determine traject path info for base %r" % base)
    return traject.get_path(model)


@global_app.component(IPath, [Request, IApp])
def app_path(request, model):
    return model.name


@global_app.component(IModelBase, [IApp])
def app_base(model):
    return model.parent


@global_app.component(IPath, [Request, IRoot])
def root_path(request, model):
    return ''


@global_app.component(ILookup, [IApp])
def app_lookup(model):
    return Lookup(model.class_lookup())


def get_registration(request, model):
    return IResourceRegistration.adapt(request, model,
                                       lookup=request.lookup,
                                       default=None)


@global_app.component(IContent, [Request, object])
def get_content(request, model):
    reg = get_registration(request, model)
    if reg is None:
        return None
    return reg.resource(request, model)


@global_app.component(IResponse, [Request, object])
def get_response(request, model):
    reg = get_registration(request, model)
    if reg is None:
        return None
    content = reg.resource(request, model)
    if reg.render is None:
        return content
    return reg.render(content)
