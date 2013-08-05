from .interfaces import IRoot
from .registry import Registry, Directive
from .resource import register_resource
from .traject import register_model

def add_directive(name, directive):
    def method(self, *args, **kw):
        return directive(self, *args, **kw)
    setattr(Registry, name, method)
    
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
add_directive('model', ModelDirective)

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
add_directive('resource', ResourceDirective)

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
add_directive('app', AppDirective)

class ComponentDirective(Directive):
    def __init__(self, registry, target, sources):
        self.registry = registry
        self.target = target
        self.sources = sources

    def discriminator(self):
        return ('component', self.model, self.name)

    def register(self, name, obj):
        self.registry.register(self.target, self.sources, obj)
add_directive('component', ComponentDirective)
