import venusian
from .interfaces import IConfigItem, IRoot, IConsumer
from .resource import register_resource
from .traject import register_model, TrajectConsumer

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
    def __init__(self, registry):
        self.registry = registry
        self.actions = []

    def scan(self, package):
        scanner = venusian.Scanner(config=self)
        scanner.scan(package)
        
    def action(self, item, name, obj):
        self.actions.append((item, name, obj))

    def validate(self):
        pass # XXX check for conflicts

    def commit(self):
        # XXX should traject consumer be registered here? or hook
        # it up with a special directive?
        self.registry.register(IConsumer, (object,),
                               TrajectConsumer(self.registry)) 
        
        for item, name, obj in self.actions:
            item.register(self.registry, name, obj)

class model(Directive):
    def __init__(self, base, model, path, variables):
        self.base = base
        self.model = model
        self.path = path
        self.variables = variables

    def discriminator(self):
        # a model can only be made available once for a base
        return ('model', self.base, self.model)

    def register(self, registry, name, obj):    
        register_model(registry, self.base, self.model, self.path,
                       self.variables, obj)
    
class resource(Directive):
    def __init__(self, model, name=''):
        self.model = model
        self.name = name
        self.predicates = {
            'name': self.name
            }

    def discriminator(self):
        return ('resource', self.model, self.name)
    
    def register(self, registry, name, obj):
        register_resource(registry, self.model, obj, **self.predicates)

# XXX can implement as subclass of model instead
class app(Directive):
    def __init__(self, model, name):
        self.model = model
        self.name = name

    def discriminator(self):
        return ('app', self.model, self.name)

    def register(self, registry, name, obj):    
        register_model(registry, IRoot, self.model, self.name,
                       lambda app: {}, obj)

