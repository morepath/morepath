from .publish import publish
from .request import Request
from .traject import Traject
from .config import Action
from reg import ClassRegistry, Lookup, ChainClassLookup, CachingClassLookup
import venusian
from werkzeug.serving import run_simple


class App(Action, ClassRegistry):
    # XXX split path parent from configuration parent
    def __init__(self, name='', parent=None):
        super(App, self).__init__()
        self.name = name
        self.child_apps = {}
        self.parent = parent
        self.traject = Traject()
        if self.parent is not None:
            parent.add_child(self)

        # allow being scanned by venusian
        def callback(scanner, name, obj):
            scanner.config.action(self, self)
        venusian.attach(self, callback)

    def discriminator(self):
        return None

    # XXX clone() isn't right, as we'd actually put things in a traject of
    # cloned?

    def perform(self, obj):
        if self.parent is None:
            return
        self.parent.traject.add_pattern(
            self.name, lambda: self)

    def clear(self):
        super(App, self).clear()
        self.traject = Traject()
        # for child_app in self.child_apps.values():
        #     child_app.clear()

    def add_child(self, app):
        self.child_apps[app.name] = app

    def class_lookup(self):
        if self.parent is None:
            return ChainClassLookup(self, global_app)
        return ChainClassLookup(self, self.parent.class_lookup())

    def lookup(self):
        # XXX instead of a separate cache we could put caching in here
        return app_lookup_cache.get(self)

    def request(self, environ):
        request = Request(environ)
        request.lookup = self.lookup()
        return request

    def __call__(self, environ, start_response):
        request = self.request(environ)
        request.lookup = self.lookup()
        response = publish(request, self)
        return response(environ, start_response)

    def run(self, host=None, port=None, **options):
        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = 5000
        run_simple(host, port, self, **options)


class AppLookupCache(object):
    def __init__(self):
        self.cache = {}

    def get(self, app):
        lookup = self.cache.get(app)
        if lookup is not None:
            return lookup
        class_lookup = app.class_lookup()
        caching_class_lookup = CachingClassLookup(class_lookup)
        result = self.cache[app] = Lookup(caching_class_lookup)
        return result

global_app = App()

app_lookup_cache = AppLookupCache()
