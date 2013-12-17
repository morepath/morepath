from .app import AppBase
from .config import Directive
from .error import ConfigError
from .view import (register_view, render_json, render_html,
                   register_predicate)
from .security import (register_permission_checker,
                       register_identity_policy, Identity, NoIdentity)
from .model import register_model, register_root, register_mount
from .traject import Path
from reg import KeyIndex


class directive(object):
    """Register a new directive with Morepath.

    Instantiate this class with the name of the configuration directive.
    The instance is a decorator that can be applied to a subclass of
    :class:`Directive`. For example::

      @directive('foo')
      class FooDirective(Directive):
         ...

    This needs to be executed *before* the directive is being used and
    thus might introduce import dependency issues unlike normal Morepath
    configuration: beware!
    """
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


@directive('permission')
class PermissionDirective(Directive):
    def __init__(self, app,  model, permission, identity=Identity):
        super(PermissionDirective, self).__init__(app)
        self.model = model
        self.permission = permission
        if identity is None:
            identity = NoIdentity
        self.identity = identity

    def identifier(self):
        return ('permission', self.model, self.permission, self.identity)

    def perform(self, app, obj):
        register_permission_checker(
            app, self.identity, self.model, self.permission, obj)


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
        register_view(app, self.model, obj, self.render, self.permission,
                      self.predicates)


@directive('predicate')
class PredicateDirective(Directive):
    priority = 1000 # execute earlier than view directive

    def __init__(self, app, name, order, index=KeyIndex):
        super(PredicateDirective, self).__init__(app)
        self.name = name
        self.index = index
        self.order = order

    def identifier(self):
        return ('predicate', self.name)

    def perform(self, app, obj):
        register_predicate(app, obj, self.name, self.index, self.order)


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


@directive('identity_policy')
class IdentityPolicyDirective(Directive):
    def identifier(self):
        return ('identity_policy',)

    def perform(self, app, obj):
        register_identity_policy(app, obj())


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
