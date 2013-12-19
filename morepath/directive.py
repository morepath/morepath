from .app import AppBase
from .config import Directive
from .error import ConfigError
from .view import (register_view, render_json, render_html,
                   register_predicate)
from .security import (register_permission_checker,
                       Identity, NoIdentity)
from .model import register_model, register_root, register_mount
from .traject import Path
from reg import KeyIndex
from .request import Request, Response
from morepath import generic
from functools import update_wrapper

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
        # this is to help morepath.sphinxext to do the right thing
        method.actual_directive = directive
        update_wrapper(method, directive.__init__)
        setattr(AppBase, self.name, method)
        return directive


@directive('model')
class ModelDirective(Directive):
    def __init__(self, app,  path, model=None,
                 variables=None, base=None, get_base=None):
        """Register a model for a path.

        Decorate a function or a class (constructor). The function
        should return an instance of the model class, for instance by
        querying it from the database, or ``None`` if the model does
        not exist.

        The decorated function will get as parameters any variables
        specified in the path. If you declare a ``request`` parameter
        the function will be able to use that information too.

        :param path: the route for which the model is registered.
        :param model: the class of the model that the decorated function
          should return. If the directive is used on a class instead of a
          function, the model should not be provided.
        :param variables: a function that given a model object can construct
          the variables used in the path. Can be omitted if no variables
          are used in the path.
        :param base: the class of the base model from which routing
          should start.  If omitted, the routing will start from the
          mounted application's root.
        :param get_base: if a ``base`` parameter is provided, this should
          be a function that given the model can return an instance of the
          ``base``.
        """
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
        """Declare whether a model has a permission.

        The decorated function receives ``model``, `permission``
        (instance of any permission object) and ``identity``
        (:class:`morepath.security.Identity`) parameters. The
        decorated function should return ``True`` only if the given
        identity exists and has that permission on the model.

        :param model: the model class
        :permission model: permission class
        :identity: identity to check permission for
        """
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
                 **predicates):
        '''Register a view for a model.

        The decorated function gets a ``request``
        (:class:`morepath.Request`) and ``model`` parameter. The
        function should return either a (unicode) string that will be
        the response body, or a :class:`morepath.Response` object.

        If a specific ``render`` function is given the output of the
        function is passed to this first, and the function could
        return whatever the ``render`` parameter expects as input.
        :func:`morepath.render_json` for instance expects a Python
        object such as a dict that can be serialized to JSON.

        See also :meth:`morepath.AppBase.json`` and
        :meth:`morepath.AppBase.html`.

        :param model: the class of the model for which this view is registered.
        :param name: the name of the view as it appears in the URL. If omitted,
          it is the empty string, meaning the default view for the model.
        :param render: an optional function that can render the output of the
          view function to a response, and possibly set headers such as
          ``Content-Type``, etc.
        :param permission: a permission class. The model should have this
          permission, otherwise access to this view is forbidden. If omitted,
          the view function is public.
        :param predicates: predicates to match this view on.
        '''
        super(ViewDirective, self).__init__(app)
        self.model = model
        self.name = name
        self.render = render
        self.predicates = {
            'name': self.name
            }
        self.permission = permission
        self.kw = predicates
        self.predicates.update(predicates)

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
    priority = 1000  # execute earlier than view directive

    def __init__(self, app, name, order, default, index=KeyIndex):
        """Register custom view predicate.

        The decorated function gets ``request`` (a
        :class:`morepath.Request` object) and ``model``
        parameters. From this information it should calculate a
        predicate value and return it. You can then pass these extra
        predicate arguments to :meth:`morepath.AppBase.view` and this
        view will only be found if the predicate matches.

        :param name: the name of the view predicate.
        :param order: when this custom view predicate should be checked
          compared to the others. A lower order means a higher importance.
        :type order: int
        :param default: the default value for this view predicate.
          This is used when using :meth:`Request.view` to render a view;
          otherwise the value will be derived from request and model.
        :param index: the predicate index to use. Default is :class:`reg.KeyIndex`
          which matches by name.
        """
        super(PredicateDirective, self).__init__(app)
        self.name = name
        self.order = order
        self.default = default
        self.index = index

    def identifier(self):
        return ('predicate', self.name)

    def perform(self, app, obj):
        register_predicate(app, self.name, self.order, self.default,
                           self.index, obj)


@directive('json')
class JsonDirective(ViewDirective):
    def __init__(self, app, model, name='', render=None,
                 permission=None, **predicates):
        """Register JSON view.

        This is like :meth:`morepath.AppBase.view`, but with
        :func:`morepath.render_json` as default for the `render`
        function.

        Transforms the view output to JSON and sets the content type to
        ``application/json``.

        :param model: the class of the model for which this view is registered.
        :param name: the name of the view as it appears in the URL. If omitted,
          it is the empty string, meaning the default view for the model.
        :param render: an optional function that can render the output of the
          view function to a response, and possibly set headers such as
          ``Content-Type``, etc. Renders as JSON by default.
        :param permission: a permission class. The model should have this
          permission, otherwise access to this view is forbidden. If omitted,
          the view function is public.
        :param predicates: predicates to match this view on.
        """
        render = render or render_json
        super(JsonDirective, self).__init__(app, model, name, render,
                                            permission, **predicates)


@directive('html')
class HtmlDirective(ViewDirective):
    def __init__(self, app, model, name='', render=None,
                 permission=None, **predicates):
        """Register HTML view.

        This is like :meth:`morepath.AppBase.view`, but with
        :func:`morepath.render_html` as default for the `render`
        function.

        Sets the content type to ``text/html``.

        :param model: the class of the model for which this view is registered.
        :param name: the name of the view as it appears in the URL. If omitted,
          it is the empty string, meaning the default view for the model.
        :param render: an optional function that can render the output of the
          view function to a response, and possibly set headers such as
          ``Content-Type``, etc. Renders as HTML by default.
        :param permission: a permission class. The model should have this
          permission, otherwise access to this view is forbidden. If omitted,
          the view function is public.
        :param predicates: predicates to match this view on.
        """
        render = render or render_html
        super(HtmlDirective, self).__init__(app, model, name, render,
                                            permission, **predicates)


@directive('root')
class RootDirective(Directive):
    def __init__(self, app, model=None):
        """Register the root model.

        The decorated function or class (constructor) should return
        the model that will be found when the app is routed to
        directly, i.e. the empty path ``''``. The decorated function
        gets no arguments.

        :param model: the class of the root model. Should not be supplied
          if this decorates a class.
        """
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
        """Mount sub application on path.

        The decorated function gets the variables specified in path as
        parameters. It should return a dictionary with the context
        parameters for the mounted app.

        :param path: the path to mount the application on.
        :param app: the :class:`morepath.App` instance to mount.
        """
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
    def __init__(self, app):
        '''Register identity policy.

        The decorated function should return an instance of an
        identity policy, which should have ``identify``, ``remember``
        and ``forget`` methods.
        '''
        super(IdentityPolicyDirective, self).__init__(app)

    def identifier(self):
        return ('identity_policy',)

    def prepare(self, obj):
        policy = obj()
        app = self.configurable
        yield app.function(
            generic.identify, Request), policy.identify
        yield app.function(
            generic.remember, Response, Request, object), policy.remember
        yield app.function(
            generic.forget, Response, Request), policy.forget


@directive('function')
class FunctionDirective(Directive):
    def __init__(self, app, target, *sources):
        '''Register function as implementation of generic function

        The decorated function is an implementation of the generic
        function supplied to the decorator. This way you can override
        parts of the Morepath framework, or create new hookable
        functions of your own. This is a layer over
        :meth:`reg.IRegistry.register`.

        :param target: the generic function to register an implementation for.
        :type target: function object
        :param sources: classes of parameters to register for.
        '''
        super(FunctionDirective, self).__init__(app)
        self.target = target
        self.sources = tuple(sources)

    def identifier(self):
        return ('function', self.target, self.sources)

    def perform(self, app, obj):
        app.register(self.target, self.sources, obj)
