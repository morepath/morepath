from .interfaces import IRoot
from .publish import publish
from .request import Request
from comparch import ClassRegistry, Lookup, ChainClassLookup

known_apps = {}

class App(ClassRegistry):
    def __init__(self, name='', parent=None):
        super(App, self).__init__()
        self.name = name
        self.root_model = None
        self.root_obj = None
        self.sub_apps = {}
        self.parent = parent
        if self.parent is not None:
            parent.sub_apps[name] = self
    
    def __call__(self, environ, start_response):
        # XXX do caching lookup where?
        if self.parent is not None:
            class_lookup = ChainClassLookup(self, self.parent)
        else:
            class_lookup = ChainClassLookup(self, global_app)
        lookup = Lookup(class_lookup)
        request = Request(environ)
        request.lookup = lookup
        response = publish(request, self.root_obj, lookup)
        return response(environ, start_response)

global_app = App()

# XXX this shouldn't be here but be the root of the global app
class Root(IRoot):
    pass
root = Root()
