from .publish import publish
from .request import Request
from .traject import Traject
from .config import Action
from reg import ClassRegistry, Lookup, ChainClassLookup


class App(Action, ClassRegistry):
    # XXX split path parent from configuration parent
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

    def discriminator(self):
        # XXX this isn't right, as we could have multiple sub apps
        # with the same name
        return ('app', self.name)

    # XXX clone() isn't right, as we'd actually put things in a traject of
    # cloned?

    def perform(self, obj):
        if self.parent is None:
            return
        self.parent.traject.register(
            self.name, lambda: self, conflicting=True)

    def clear(self):
        super(App, self).clear()
        self.root_model = None
        self.root_obj = None
        self.traject = Traject()
        # for child_app in self.child_apps.values():
        #     child_app.clear()

    def add_child(self, app):
        self.child_apps[app.name] = app

    def class_lookup(self):
        # XXX caching needs to be introduced for at least class lookups
        # and survive multiple requests for caching to be useful
        if self.parent is None:
            return ChainClassLookup(self, global_app)
        return ChainClassLookup(self, self.parent.class_lookup())

    def lookup(self):
        return Lookup(self.class_lookup())

    def __call__(self, environ, start_response):
        request = Request(environ)
        request.lookup = self.lookup()
        response = publish(request, self)
        return response(environ, start_response)

global_app = App()
