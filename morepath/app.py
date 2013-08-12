from comparch import ClassRegistry, Lookup, ChainClassLookup
from .request import Request, Response
from .publish import publish
from .traject import traject_consumer
from .interfaces import IConsumer, IPath, IRoot, IModelBase, ITraject, LinkError

class App(ClassRegistry):
    def __init__(self, name=''):
        super(App, self).__init__()
        self.name = name
        self.root_model = None
        self.root_obj = None
        
    def __call__(self, environ, start_response):
        # XXX do caching lookup where?
        lookup = Lookup(ChainClassLookup(self, global_app))
        request = Request(environ)
        request.lookup = lookup
        response = publish(request, self.root_obj, lookup)
        return response(environ, start_response)

global_app = App()

# XXX this shouldn't be here but be the root of the global app
class Root(IRoot):
    pass
root = Root()

# XXX should be done inside a function
global_app.register(IConsumer, (object,), traject_consumer)

def traject_path(request, model):
    base = IModelBase.adapt(model, lookup=request.lookup, default=None)
    traject = ITraject.component(base, lookup=request.lookup, default=None)
    if traject is None:
        raise LinkError(
            "cannot determine traject path info for base %r" % base)
    return traject.get_path(model)
global_app.register(IPath, [Request, object], traject_path)

def app_path(request, model):
    return model.name
global_app.register(IPath, [Request, App], app_path)

def app_base(model):
    return None
global_app.register(IModelBase, [App], app_base)

def root_path(request, model):
    return ''
global_app.register(IPath, [Request, IRoot], root_path)

# model has a base. this contains the traject info

# root has separate path. this is the path of the app.
