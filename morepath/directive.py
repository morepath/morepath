import venusian
from .interfaces import IConfigItem, IRoot
from .resource import register_resource
from .traject import register_model
from comparch import Registry as BaseRegistry

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

class Registry(BaseRegistry):
    def model(self, base, model, path, variables):
        return ModelDirective(self, base, model, path, variables) 
    def resource(self, model, name=''):
        return ResourceDirective(self, model, name)
    def app(self, model, name):
        return AppDirective(self, model, name)
    
class ModelDirective(Directive):
    def __init__(self, registry, base, model, path, variables):
        self.registry = registry
        self.base = base
        self.model = model
        self.path = path
        self.variables = variables

    def discriminator(self):
        # a model can only be made available once for a base
        return ('model', self.base, self.model)

    def register(self, name, obj):    
        register_model(self.registry, self.base, self.model, self.path,
                       self.variables, obj)
    
class ResourceDirective(Directive):
    def __init__(self, registry, model, name=''):
        self.registry = registry
        self.model = model
        self.name = name
        self.predicates = {
            'name': self.name
            }

    def discriminator(self):
        return ('resource', self.model, self.name)
    
    def register(self, name, obj):
        register_resource(self.registry, self.model, obj, **self.predicates)

# XXX can implement as subclass of model instead
class AppDirective(Directive):
    def __init__(self, registry, model, name):
        self.registry = registry
        self.model = model
        self.name = name

    def discriminator(self):
        return ('app', self.model, self.name)

    def register(self, name, obj):
        register_model(self.registry, IRoot, self.model, self.name,
                       lambda app: {}, obj)

