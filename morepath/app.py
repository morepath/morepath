from .interfaces import IRoot, IApp
from .publish import publish
from .request import Request
from .traject import Traject
from comparch import ClassRegistry, Lookup, ChainClassLookup

known_apps = {}

class App(IApp, ClassRegistry):
    def __init__(self, name='', parent=None):
        super(App, self).__init__()
        self.name = name
        self.root_model = None
        self.root_obj = None
        self.child_apps = {}
        self.parent = parent
        self.traject = Traject()
        if self.parent is not None:
            parent.add_child(self)

    def add_child(self, app):
        self.child_apps[app.name] = app
        self.traject.register(app.name, lambda: app, conflicting=True)

    def class_lookup(self):
        if self.parent is None:
            return ChainClassLookup(self, global_app)
        return ChainClassLookup(self, self.parent.class_lookup())
    
    def __call__(self, environ, start_response):
        # XXX do caching lookup where?
        lookup = Lookup(self.class_lookup())
        request = Request(environ)
        request.lookup = lookup
        response = publish(request, self, lookup)
        return response(environ, start_response)

global_app = App()
