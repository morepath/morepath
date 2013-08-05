import venusian
from .interfaces import IConfigItem
from comparch import ClassRegistry

class Directive(IConfigItem):
    def discriminator(self):
        raise NotImplementedError()

    def register(self, registry, name, obj):
        raise NotImplementedError()
    
    def __call__(self, wrapped):
        def callback(scanner, name, obj):
            scanner.config.action(self, name, obj)
        venusian.attach(wrapped, callback)
        return wrapped

class Config(object):
    def __init__(self):
        self.actions = []

    def scan(self, package):
        scanner = venusian.Scanner(config=self)
        scanner.scan(package)
        
    def action(self, item, name, obj):
        self.actions.append((item, name, obj))

    def validate(self):
        pass # XXX check for conflicts

    def commit(self):
        for item, name, obj in self.actions:
            item.register(name, obj)

class Registry(ClassRegistry):
    pass

class directive(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, directive):
        def method(self, *args, **kw):
            return directive(self, *args, **kw)
        setattr(Registry, self.name, method)

