from .app import App
from .config import Directive
from .error import ConfigError
from .view import register_view, render_json, render_html
from .traject import register_model, register_root


class directive(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, directive):
        def method(self, *args, **kw):
            return directive(self, *args, **kw)
        setattr(App, self.name, method)
        return directive


@directive('model')
class ModelDirective(Directive):
    def __init__(self, app,  path, model=None,
                 variables=None, base=None, get_base=None):
        self.app = app
        self.model = model
        self.path = path
        self.variables = variables
        self.base = base
        self.get_base = get_base

    def discriminator(self):
        return ('model', self.app, self.model)

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


@directive('view')
class ViewDirective(Directive):
    def __init__(self, app, model, name='', render=None, **kw):
        self.app = app
        self.model = model
        self.name = name
        self.render = render
        self.predicates = {
            'name': self.name
            }
        self.predicates.update(kw)

    def discriminator(self):
        predicates_discriminator = tuple(sorted(self.predicates.items()))
        return ('view', self.app, self.model, self.name,
                predicates_discriminator)

    def perform(self, obj):
        register_view(self.app, self.model, obj, self.render,
                      self.predicates)


@directive('json')
class JsonDirective(ViewDirective):
    def __init__(self, app, model, name='', render=render_json, **kw):
        super(JsonDirective, self).__init__(app, model, name, render, **kw)


@directive('html')
class HtmlDirective(ViewDirective):
    def __init__(self, app, model, name='', render=render_html, **kw):
        super(HtmlDirective, self).__init__(app, model, name, render, **kw)


@directive('root')
class RootDirective(Directive):
    def __init__(self, app, model=None):
        self.app = app
        self.model = model

    def discriminator(self):
        return ('root', self.app)

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


@directive('function')
class FunctionDirective(Directive):
    def __init__(self, app, target, *sources):
        self.app = app
        self.target = target
        self.sources = tuple(sources)

    def discriminator(self):
        return ('function', self.app, self.target, self.sources)

    def perform(self, obj):
        self.app.register(self.target, self.sources, obj)
