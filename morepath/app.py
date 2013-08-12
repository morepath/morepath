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
