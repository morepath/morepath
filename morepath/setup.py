import morepath
from .config import Config
from interfaces import ITraject, IConsumer, IModelBase, IRoot, IPath, LinkError
from .app import global_app, Root, App
from .request import Request
from .traject import traject_consumer

def setup():
    config = Config()
    config.scan(morepath, ignore=['.tests'])
    config.commit()
    # XXX could be registered with @component too
    global_app.register(IConsumer, [object], traject_consumer)
    
@global_app.component(IPath, [Request, object])
def traject_path(request, model):
    base = IModelBase.adapt(model, lookup=request.lookup, default=None)
    traject = ITraject.component(base, lookup=request.lookup, default=None)
    if traject is None:
        raise LinkError(
            "cannot determine traject path info for base %r" % base)
    return traject.get_path(model)

@global_app.component(IPath, [Request, App])
def app_path(request, model):
    return model.name

@global_app.component(IModelBase, [App])
def app_base(model):
    return None

@global_app.component(IPath, [Request, IRoot])
def root_path(request, model):
    return ''
