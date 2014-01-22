from .app import AppBase
from .config import Directive
from .error import ConfigError
from .view import (register_view, render_json, render_html,
                   register_predicate, register_predicate_fallback,
                   get_predicates_with_defaults)
from .security import (register_permission_checker,
                       Identity, NoIdentity)
from .path import register_path, register_mount
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
    configuration, so beware!
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

@directive('converter')
class ConverterDirective(Directive):
    def __init__(self, app, type):
        """Register custom converter for type.

        :param type: the Python type for which to register the
          converter.  Morepath uses converters when converting path
          variables and URL parameters when decoding or encoding
          URLs. Morepath will look up the converter using the
          type. The type is either given explicitly as the value in
          the ``converters`` dictionary in the
          :meth:`morepath.AppBase.path` directive, or is deduced from
          the value of the default argument of the decorated model
          function or class using ``type()``.
        """
        super(ConverterDirective, self).__init__(app)
        self.type = type

    def identifier(self, app):
        return ('converter', self.type)

    def perform(self, app, obj):
        app.register_converter(self.type, obj())


@directive('path')
class PathDirective(Directive):
    depends = [ConverterDirective]

    def __init__(self, app,  path, model=None,
                 variables=None, converters=None, required=None):
        """Register a model for a path.

        Decorate a function or a class (constructor). The function
        should return an instance of the model class, for instance by
        querying it from the database, or ``None`` if the model does
        not exist.

        The decorated function will get as arguments any variables
        specified in the path as well as URL parameters.

        If you declare a ``request`` parameter the function will be
        able to use that information too.

        :param path: the route for which the model is registered.
        :param model: the class of the model that the decorated function
          should return. If the directive is used on a class instead of a
          function, the model should not be provided.
        :param variables: a function that given a model object can construct
          the variables used in the path (including any URL parameters).
          If omitted, variables are retrieved from the model by using
          the arguments of the decorated function.
        :param converters: a dictionary containing converters for variables.
          The key is the variable name, the value is a
          :class:`morepath.Converter` instance.
        :param required: list or set of names of those URL parameters which
           should be required, i.e. if missing a 400 Bad Request response will
           be given. Any default value is ignored. Has no effect on path
           variables. Optional.
        """
        super(PathDirective, self).__init__(app)
        self.model = model
        self.path = path
        self.variables = variables
        self.converters = converters
        self.required = required

    def identifier(self, app):
        return ('path', Path(self.path).discriminator())

    def discriminators(self, app):
        return [('model', self.model)]

    def prepare(self, obj):
        # XXX check shared with @root
        model = self.model
        if isinstance(obj, type):
            if model is not None:
                raise ConfigError(
                    "@path decorates class so cannot "
                    "have explicit model: %s" % model)
            model = obj
        if model is None:
            raise ConfigError(
                "@path does not decorate class and has no explicit model")
        yield self.clone(model=model), obj

    def perform(self, app, obj):
        register_path(app, self.model, self.path,
                      self.variables, self.converters, self.required,
                      obj)


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
        :param permission: permission class
        :param identity: identity to check permission for. If ``None``,
          the identity to check for will be the special
          :data:`morepath.security.NO_IDENTITY`.
        """
        super(PermissionDirective, self).__init__(app)
        self.model = model
        self.permission = permission
        if identity is None:
            identity = NoIdentity
        self.identity = identity

    def identifier(self, app):
        return (self.model, self.permission, self.identity)

    def perform(self, app, obj):
        register_permission_checker(
            app, self.identity, self.model, self.permission, obj)



@directive('predicate')
class PredicateDirective(Directive):
    def __init__(self, app, name, order, default, index=KeyIndex):
        """Register custom view predicate.

        The decorated function gets ``model`` and ``request`` (a
        :class:`morepath.Request` object) parameters.

        From this information it should calculate a predicate value
        and return it. You can then pass these extra predicate
        arguments to :meth:`morepath.AppBase.view` and this view will
        only be found if the predicate matches.

        :param name: the name of the view predicate.
        :param order: when this custom view predicate should be checked
          compared to the others. A lower order means a higher importance.
        :type order: int
        :param default: the default value for this view predicate.
          This is used when the predicate is omitted or ``None`` when
          supplied to the :meth:`morepath.AppBase.view` directive.
          This is also used when using :meth:`Request.view` to render
          a view.
        :param index: the predicate index to use. Default is
          :class:`reg.KeyIndex` which matches by name.
        """
        super(PredicateDirective, self).__init__(app)
        self.name = name
        self.order = order
        self.default = default
        self.index = index

    def identifier(self, app):
        return self.name

    def perform(self, app, obj):
        register_predicate(app, self.name, self.order, self.default,
                           self.index, obj)


@directive('predicate_fallback')
class PredicateFallbackDirective(Directive):
    depends = [PredicateDirective]

    def __init__(self, app, name):
        super(PredicateFallbackDirective, self).__init__(app)
        self.name = name

    def identifier(self, app):
        return self.name

    def perform(self, app, obj):
        register_predicate_fallback(app, self.name, obj)


@directive('view')
class ViewDirective(Directive):
    depends = [PredicateDirective, PredicateFallbackDirective]

    def __init__(self, app, model, name=None, render=None, permission=None,
                 **predicates):
        '''Register a view for a model.

        The decorated function gets ``model`` and``request``
        (:class:`morepath.Request`) parameters. The function should
        return either a (unicode) string that will be the response
        body, or a :class:`morepath.Response` object.

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
        :param predicates: predicates to match this view on. Use
           :data:`morepath.ANY` for a predicate if you don't care what
           the value is. If you don't specify a predicate, the default
           value will be used.
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

    def identifier(self, app):
        predicates = get_predicates_with_defaults(
           self.predicates, app.exact('predicate_info', ()))
        predicates_discriminator = tuple(sorted(predicates.items()))
        return (self.model, predicates_discriminator)

    def perform(self, app, obj):
        register_view(app, self.model, obj, self.render, self.permission,
                      self.predicates)


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


@directive('mount')
class MountDirective(PathDirective):
    depends = [ConverterDirective]
    def __init__(self, base_app, path, app, converters=None,
                 required=None):
        """Mount sub application on path.

        The decorated function gets the variables specified in path as
        parameters. It should return a dictionary with the required
        variables for the mounted app. The variables are declared in
        the :class:`morepath.App` constructor.

        :param path: the path to mount the application on.
        :param app: the :class:`morepath.App` instance to mount.
        :param converters: converters as for the
          :meth:`morepath.AppBase.path` directive.
        :param required: list or set of names of those URL parameters which
          should be required, i.e. if missing a 400 Bad Request response will
          be given. Any default value is ignored. Has no effect on path
          variables. Optional.
        """
        super(MountDirective, self).__init__(base_app, path,
                                             converters=converters,
                                             required=required)
        self.mounted_app = app

    # XXX it's a bit of a hack to make the mount directive
    # group with the path directive so we get conflicts,
    # we need to override prepare to shut it up again
    def prepare(self, obj):
        yield self.clone(), obj

    def discriminators(self, app):
        return [('mount', self.mounted_app)]

    def perform(self, app, obj):
        register_mount(app, self.mounted_app, self.path, self.required, obj)


@directive('identity_policy')
class IdentityPolicyDirective(Directive):
    def __init__(self, app):
        '''Register identity policy.

        The decorated function should return an instance of an
        identity policy, which should have ``identify``, ``remember``
        and ``forget`` methods.
        '''
        super(IdentityPolicyDirective, self).__init__(app)

    def identifier(self, app):
        # there can be only one
        return None

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

    def identifier(self, app):
        return (self.target, self.sources)

    def perform(self, app, obj):
        app.register(self.target, self.sources, obj)
