from .app import global_app
from .config import Config
import morepath.directive #
from .interfaces import (ITraject, IConsumer, ILookup, IModelBase, IRoot,
                         IPath, LinkError, IApp)
from .pathstack import DEFAULT
from .request import Request
from .traject import traject_consumer
import morepath
from comparch import Lookup

assert morepath.directive # we need to make the component directive work

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

