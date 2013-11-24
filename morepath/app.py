from .publish import publish, Mount
from .request import Request
from .traject import Traject
from .config import Action
from reg import ClassRegistry, Lookup, ChainClassLookup, CachingClassLookup
import venusian
from werkzeug.serving import run_simple


class App(Action, ClassRegistry):
    # XXX split path parent from configuration parent
    # XXX have a way to define parameters for app here
    def __init__(self, name='', extends=None):
        super(App, self).__init__()
        self.name = name
        self.extends = extends
        self.traject = Traject()

        # allow being scanned by venusian
        def callback(scanner, name, obj):
            scanner.config.action(self, self)
        venusian.attach(self, callback)

    def __repr__(self):
        return '<morepath.App %r>' % self.name

    def discriminator(self):
        return None

    # XXX clone() isn't right, as we'd actually put things in a traject of
    # cloned?

    def perform(self, obj):
        pass

    def clear(self):
        super(App, self).clear()
        self.traject = Traject()

    def class_lookup(self):
        if not self.extends:
            return ChainClassLookup(self, global_app)
        return ChainClassLookup(result, self.extends.class_lookup())

    def lookup(self):
        # XXX instead of a separate cache we could put caching in here
        return app_lookup_cache.get(self)

    def request(self, environ):
        request = Request(environ)
        request.lookup = self.lookup()
        request.unconsumed = []
        return request

    def context(self, d):
        def wsgi(environ, start_response):
            return self(environ, start_response, context=d)
        return wsgi

    def mounted(self, context=None):
        context = context or {}
        return Mount(self, lambda: context, {})

    def __call__(self, environ, start_response, context=None):
        request = self.request(environ)
        response = publish(request, self.mounted(context))
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
