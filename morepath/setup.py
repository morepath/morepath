from .app import App, global_app
from .config import Config
import morepath.directive #
from .interfaces import ITraject, IConsumer, IModelBase, IRoot, IPath, LinkError
from .pathstack import DEFAULT
from .request import Request
from .traject import traject_consumer
import morepath

assert morepath.directive # we need to make the component directive work

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
    return model.parent

@global_app.component(IPath, [Request, IRoot])
def root_path(request, model):
    return ''

@global_app.component(IConsumer, [App])
def app_consumer(base, stack, lookup):
    ns, name = stack.pop()
    if ns != DEFAULT:
        stack.append((ns, name))
        return False, base, stack
    app = base.child_apps.get(name)
    if app is None:
        stack.append((ns, name))
        return False, base, stack
    return True, app, stack
