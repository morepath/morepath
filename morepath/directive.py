from .interfaces import IRoot
from .registry import Directive, directive
from .resource import register_resource
from .traject import register_model

@directive('model')
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
@directive('resource')
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
@directive('app')
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

@directive('component')
class ComponentDirective(Directive):
    def __init__(self, registry, target, sources):
        self.registry = registry
        self.target = target
        self.sources = sources

    def discriminator(self):
        return ('component', self.model, self.name)

    def register(self, name, obj):
        self.registry.register(self.target, self.sources, obj)
