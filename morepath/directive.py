from .app import App
from .config import Directive
from .interfaces import ConfigError
from .resource import register_resource
from .traject import register_model, register_root


class directive(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, directive):
        def method(self, *args, **kw):
            return directive(self, *args, **kw)
        setattr(App, self.name, method)


@directive('model')
class ModelDirective(Directive):
    def __init__(self, app, model, path,
                 variables=None, base=None, get_base=None):
        self.app = app
        self.model = model
        self.path = path
        self.variables = variables
        self.base = base
        self.get_base = get_base

    def discriminator(self):
        # XXX is wrong
        # a model can only be made available once for a base
        return ('model', self.base, self.model)

    def prepare(self, obj):
        # XXX check shared with @root
        if isinstance(obj, type):
            if self.model is not None:
                raise ConfigError(
                    "@model decorates class so cannot "
                    "have explicit model: %s" % self.model)
            self.model = obj
        if self.model is None:
            raise ConfigError(
                "@model does not decorate class and has no explicit model")

        # XXX check whether get_base is there if base is there
        # XXX check whether variables is there if variable is used in
        # path

    def perform(self, obj):
        register_model(self.app, self.model, self.path,
                       self.variables, obj, self.base, self.get_base)


@directive('resource')
class ResourceDirective(Directive):
    def __init__(self, app, model, name='', render=None):
        self.app = app
        self.model = model
        self.name = name
        self.render = render
        self.predicates = {
            'name': self.name
            }

    def discriminator(self):
        return ('resource', self.model, self.name)

    def perform(self, obj):
        # XXX kwargs for predicates doesn't seem useful as we unpack
        # them again on the other side
        register_resource(self.app, self.model, obj, self.render,
                          self.predicates)


@directive('root')
class RootDirective(Directive):
    def __init__(self, app, model=None):
        self.app = app
        self.model = model

    def discriminator(self):
        # XXX what if model is set through a class decorator?
        return ('app', self.model, self.name)

    def prepare(self, obj):
        if isinstance(obj, type):
            if self.model is not None:
                raise ConfigError(
                    "@root decorates class so cannot have explicit model: %s" %
                    self.model)
            self.model = obj
        if self.model is None:
            raise ConfigError(
                "@root does not decorate class and has no explicit model")
        self.app.root_model = self.model
        # XXX calling things too early?
        self.app.root_obj = obj()

    def perform(self, obj):
        register_root(self.app, self.model, obj)


@directive('component')
class ComponentDirective(Directive):
    def __init__(self, app, target, sources):
        self.app = app
        self.target = target
        self.sources = sources

    def discriminator(self):
        return ('component', self.model, self.name)

    def perform(self, obj):
        self.app.register(self.target, self.sources, obj)
