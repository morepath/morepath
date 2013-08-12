import venusian
from .interfaces import IConfigItem
from .app import App

class Directive(IConfigItem):
    def discriminator(self):
        raise NotImplementedError()

    def prepare(self, name, obj):
        pass
    
    def register(self, name, obj):
        raise NotImplementedError()
    
    def __call__(self, wrapped):
        def callback(scanner, name, obj):
            scanner.config.action(self, name, obj)
        venusian.attach(wrapped, callback)
        return wrapped

class Config(object):
    def __init__(self):
        self.actions = []

    def scan(self, package, ignore=None):
        scanner = venusian.Scanner(config=self)
        scanner.scan(package, ignore=ignore)
        
    def action(self, item, name, obj):
        self.actions.append((item, name, obj))

    def validate(self):
        # XXX check for conflicts
        # XXX check that all base of an app is another app,
        # can only do this in the end
        # XXX a model cannot be registered multiple times in the same
        # registry. same for app
        # XXX check that a model registration that has a base that is
        # not an app supplies a get_base
        pass
    
    def commit(self):
        for item, name, obj in self.actions:
            item.prepare(name, obj)
        
        for item, name, obj in self.actions:
            item.register(name, obj)

class directive(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, directive):
        def method(self, *args, **kw):
            return directive(self, *args, **kw)
        setattr(App, self.name, method)

