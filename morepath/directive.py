from .app import AppBase
from .config import Directive
from .error import ConfigError
from .view import register_view, render_json, render_html
from .model import register_model, register_root, register_mount
from .traject import Path


class directive(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, directive):
        def method(self, *args, **kw):
            return directive(self, *args, **kw)
        setattr(AppBase, self.name, method)
        return directive


@directive('model')
class ModelDirective(Directive):
    def __init__(self, app,  path, model=None,
                 variables=None, base=None, get_base=None):
        super(ModelDirective, self).__init__(app)
        self.model = model
        self.path = path
        self.variables = variables
        self.base = base
        self.get_base = get_base

    def identifier(self):
        return ('path', self.base, Path(self.path).discriminator())

    def discriminators(self):
        return [('model', self.model)]

    def prepare(self, obj):
        # XXX check shared with @root
        model = self.model
        if isinstance(obj, type):
            if model is not None:
                raise ConfigError(
                    "@model decorates class so cannot "
                    "have explicit model: %s" % model)
            model = obj
        if model is None:
            raise ConfigError(
                "@model does not decorate class and has no explicit model")
        yield self.clone(model=model), obj
        # XXX check whether get_base is there if base is there
        # XXX check whether variables is there if variable is used in
        # path

    def perform(self, app, obj):
        register_model(app, self.model, self.path,
                       self.variables, obj, self.base, self.get_base)


@directive('view')
class ViewDirective(Directive):
    def __init__(self, app, model, name='', render=None, permission=None,
                 **kw):
        super(ViewDirective, self).__init__(app)
        self.model = model
        self.name = name
        self.render = render
        self.predicates = {
            'name': self.name
            }
        self.permission = permission
        self.kw = kw
        self.predicates.update(kw)

    def clone(self, **kw):
        # XXX standard clone doesn't work due to use of predicates
        # non-immutable in __init__. move this to another phase so
        # that this more complex clone isn't needed?
        args = dict(
            app=self.configurable,
            model=self.model,
            name=self.name,
            render=self.render,
            permission=self.permission)
        args.update(self.kw)
        args.update(kw)
        return ViewDirective(**args)

    def identifier(self):
        predicates_discriminator = tuple(sorted(self.predicates.items()))
        return ('view', self.model, self.name, predicates_discriminator)

    def perform(self, app, obj):
        register_view(app, self.model, obj, self.render,
                      self.predicates)


@directive('json')
class JsonDirective(ViewDirective):
    def __init__(self, app, model, name='', render=render_json,
                 permission=None, **kw):
        super(JsonDirective, self).__init__(app, model, name, render,
                                            permission, **kw)


@directive('html')
class HtmlDirective(ViewDirective):
    def __init__(self, app, model, name='', render=render_html,
                 permission=None, **kw):
        super(HtmlDirective, self).__init__(app, model, name, render,
                                            permission, **kw)


@directive('root')
class RootDirective(Directive):
    def __init__(self, app, model=None):
        super(RootDirective, self).__init__(app)
        self.model = model

    def identifier(self):
        return ('root',)

    def prepare(self, obj):
        model = self.model
        if isinstance(obj, type):
            if model is not None:
                raise ConfigError(
                    "@root decorates class so cannot have explicit model: %s" %
                    model)
            model = obj
        if model is None:
            raise ConfigError(
                "@root does not decorate class and has no explicit model")
        yield self.clone(model=model), obj

    def perform(self, app, obj):
        register_root(app, self.model, obj)


@directive('mount')
class MountDirective(Directive):
    def __init__(self, base_app,  path, app):
        super(MountDirective, self).__init__(base_app)
        self.mounted_app = app
        self.path = path

    def identifier(self):
        return ('path', Path(self.path).discriminator())

    def discriminators(self):
        return [('mount', self.mounted_app)]

    def perform(self, app, obj):
        register_mount(app, self.mounted_app, self.path, obj)


@directive('function')
class FunctionDirective(Directive):
    def __init__(self, app, target, *sources):
        super(FunctionDirective, self).__init__(app)
        self.target = target
        self.sources = tuple(sources)

    def identifier(self):
        return ('function', self.target, self.sources)

    def perform(self, app, obj):
        app.register(self.target, self.sources, obj)
