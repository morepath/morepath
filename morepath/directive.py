import os
from .app import App, Registry
import dectate
from .settings import register_setting
from .security import (register_permission_checker,
                       Identity, NoIdentity)
from .view import render_view, render_json, render_html, register_view
from .path import register_path
from .traject import Path
from morepath import generic
from reg import mapply


DEFAULT_CONFIG = {
    'registry': Registry
}


@App.directive('setting')
class SettingAction(dectate.Action):
    config = DEFAULT_CONFIG

    def __init__(self, section, name):
        """Register application setting.

        An application setting is registered under the ``settings``
        attribute of :class:`morepath.app.Registry`. It will
        be executed early in configuration so other configuration
        directives can depend on the settings being there.

        The decorated function returns the setting value when executed.

        :param section: the name of the section the setting should go
          under.
        :param name: the name of the setting in its section.
        """
        self.section = section
        self.name = name

    def identifier(self, registry):
        return self.section, self.name

    def perform(self, obj, registry):
        register_setting(registry, self.section, self.name, obj)

    @staticmethod
    def after(registry):
        registry.register_function(generic.settings,
                                   lambda: registry.settings)


class SettingValue(object):
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return self.value


@App.directive('setting_section')
class SettingSectionAction(dectate.Composite):
    def __init__(self, section):
        """Register application setting in a section.

        An application settings are registered under the ``settings``
        attribute of :class:`morepath.app.Registry`. It will
        be executed early in configuration so other configuration
        directives can depend on the settings being there.

        The decorated function returns a dictionary with as keys the
        setting names and as values the settings.

        :param section: the name of the section the setting should go
          under.
        """
        self.section = section

    def actions(self, obj):
        section = obj()
        for name, value in section.items():
            yield (SettingAction(section=self.section, name=name),
                   SettingValue(value))


# XXX this allows predicate_fallback directives to be installed without
# predicate directives, which has no meaning. Not sure how to detect
# this.
@App.directive('predicate_fallback')
class PredicateFallbackAction(dectate.Action):
    config = DEFAULT_CONFIG

    depends = [SettingAction]

    def __init__(self, dispatch, func):
        """For a given dispatch and function dispatched to, register fallback.

        The fallback is called with the same arguments as the dispatch
        function. It should return a response (or raise an exception
        that can be turned into a response).

        :param dispatch: the dispatch function
        :param func: the registered function we are the fallback for
        """
        self.dispatch = dispatch
        self.func = func

    def identifier(self, registry):
        return self.dispatch.wrapped_func, self.func

    def perform(self, obj, registry):
        registry.register_predicate_fallback(self.dispatch, self.func, obj)


@App.directive('predicate')
class PredicateAction(dectate.Action):
    config = DEFAULT_CONFIG

    depends = [SettingAction, PredicateFallbackAction]

    def __init__(self, dispatch, name, default, index,
                 before=None, after=None):
        """Register custom predicate for a predicate_dispatch function.

        The function registered should have arguments that are the
        same or a subset of the arguments of the predicate_dispatch
        function. From these arguments it should determine a predicate
        value and return it. The predicates for a predicate_dispatch
        function are ordered by their before and after arguments.

        You can then register a function to dispatch to using the
        :meth:`App.function` directive. This takes the
        predicate_dispatch or dispatch function as its first argument
        and the predicate key to match on as its other arguments.

        :param dispatch: the predicate_dispatch function this predicate
           is for.
        :param name: the name of the predicate. This is used when
          constructing a predicate key from a predicate dictionary.
        :param default: the default value for a predicate, in case the
          value is missing in the predicate dictionary.
        :param index: the index to use. Typically morepath.KeyIndex or
          morepath.ClassIndex.
        :param default: the default value for this predicate. This is
          used as a default value if the argument is ommitted.
        :param before: predicate function this function wants to have
           priority over.
        :param after: predicate function we want to have priority over
           this one.
        """
        self.dispatch = dispatch
        self.name = name
        self.default = default
        self.index = index
        self.before = before
        self._after = after

    def identifier(self, registry):
        return self.dispatch.wrapped_func, self.before, self._after

    def perform(self, obj, registry):
        if not self.dispatch.external_predicates:
            raise dectate.DirectiveError(
                "@predicate decorator may only be used with "
                "@reg.dispatch_external_predicates: %s" % self.dispatch)

        registry.register_predicate(obj, self.dispatch,
                                    self.name, self.default, self.index,
                                    self.before, self._after)

    @staticmethod
    def after(registry):
        registry.install_predicates()


@App.directive('function')
class FunctionAction(dectate.Action):
    config = DEFAULT_CONFIG

    depends = [SettingAction,
               PredicateAction, PredicateFallbackAction]

    def __init__(self, func, **kw):
        '''Register function as implementation of generic dispatch function

        The decorated function is an implementation of the generic
        function supplied to the decorator. This way you can override
        parts of the Morepath framework, or create new hookable
        functions of your own.

        The ``func`` argument is a generic dispatch function, so a
        Python function marked with :func:`app.dispatch` or
        :func:`app.predicate_dispatch`.

        :param func: the generic function to register an implementation for.
        :type func: dispatch function object
        :param kw: keyword parameters with the predicate keys to
           register for.  Argument names are predicate names, values
           are the predicate values to match on.
        '''
        self.func = func
        self.key_dict = kw

    def predicate_key(self, registry):
        # XXX either reg should keep track of dispatch and
        # dispatch_external_predicates functions that have been used,
        # or we should only allow their registration through a special
        # Morepath directive so that we can.
        if self.func.external_predicates and not registry.get_predicates(
                self.func):
            registry.register_external_predicates(self.func, [])
        registry.register_dispatch(self.func)
        return registry.key_dict_to_predicate_key(
            self.func.wrapped_func, self.key_dict)

    def identifier(self, registry):
        return (self.func.wrapped_func, self.predicate_key(registry))

    def perform(self, obj, registry):
        registry.register_function(self.func, obj, **self.key_dict)


@App.directive('converter')
class ConverterAction(dectate.Action):
    config = DEFAULT_CONFIG

    depends = [SettingAction]

    def __init__(self, type):
        """Register custom converter for type.

        :param type: the Python type for which to register the
          converter.  Morepath uses converters when converting path
          variables and URL parameters when decoding or encoding
          URLs. Morepath looks up the converter using the
          type. The type is either given explicitly as the value in
          the ``converters`` dictionary in the
          :meth:`morepath.App.path` directive, or is deduced from
          the value of the default argument of the decorated model
          function or class using ``type()``.
        """
        self.type = type

    def identifier(self, registry):
        return ('converter', self.type)

    def perform(self, obj, registry):
        registry.register_converter(self.type, obj())


@App.directive('path')
class PathAction(dectate.Action):
    config = DEFAULT_CONFIG

    depends = [SettingAction, ConverterAction]

    def __init__(self, path, model=None,
                 variables=None, converters=None, required=None,
                 get_converters=None, absorb=False):
        """Register a model for a path.

        Decorate a function or a class (constructor). The function
        should return an instance of the model class, for instance by
        querying it from the database, or ``None`` if the model does
        not exist.

        The decorated function gets as arguments any variables
        specified in the path as well as URL parameters.

        If you declare a ``request`` parameter the function is
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
          should be required, i.e. if missing a 400 Bad Request response is
          given. Any default value is ignored. Has no effect on path
          variables. Optional.
        :param get_converters: a function that returns a converter dictionary.
          This function is called once during configuration time. It can
          be used to programmatically supply converters. It is merged
          with the ``converters`` dictionary, if supplied. Optional.
        :param absorb: If set to ``True``, matches any subpath that
          matches this path as well. This is passed into the decorated
          function as the ``remaining`` variable.
        """
        self.model = model
        self.path = path
        self.variables = variables
        self.converters = converters
        self.required = required
        self.get_converters = get_converters
        self.absorb = absorb

    def identifier(self, registry):
        return ('path', Path(self.path).discriminator())

    def discriminators(self, registry):
        return [('model', self.model)]

    def perform(self, obj, registry):
        model = self.model
        if isinstance(obj, type):
            if model is not None:
                raise dectate.DirectiveError(
                    "@path decorates class so cannot "
                    "have explicit model: %s" % model)
            model = obj
        if model is None:
            raise dectate.DirectiveError(
                "@path does not decorate class and has no explicit model")
        register_path(registry, model, self.path,
                      self.variables, self.converters, self.required,
                      self.get_converters, self.absorb,
                      obj)


@App.directive('permission_rule')
class PermissionRuleAction(dectate.Action):
    config = DEFAULT_CONFIG

    depends = [SettingAction]

    def __init__(self, model, permission, identity=Identity):
        """Declare whether a model has a permission.

        The decorated function receives ``model``, `permission``
        (instance of any permission object) and ``identity``
        (:class:`morepath.security.Identity`) parameters. The
        decorated function should return ``True`` only if the given
        identity exists and has that permission on the model.

        :param model: the model class
        :param permission: permission class
        :param identity: identity class to check permission for. If ``None``,
          the identity to check for is the special
          :data:`morepath.security.NO_IDENTITY`.
        """
        self.model = model
        self.permission = permission
        if identity is None:
            identity = NoIdentity
        self.identity = identity

    def identifier(self, registry):
        return (self.model, self.permission, self.identity)

    def perform(self, obj, registry):
        register_permission_checker(
            registry, self.identity, self.model, self.permission, obj)


template_directory_id = 0


@App.directive('template_directory')
class TemplateDirectoryAction(dectate.Action):
    config = DEFAULT_CONFIG

    depends = [SettingAction]

    def __init__(self, after=None, before=None, name=None):
        '''Register template directory.

        The decorated function gets no argument and should return a
        relative or absolute path to a directory containing templates
        that can be loaded by this app. If a relative path, it is made
        absolute from the directory this module is in.

        Template directories can be ordered: templates in a directory
        ``before`` another one are found before templates in a
        directory ``after`` it. But you can leave both ``before`` and
        ``after`` out: template directories defined in
        sub-applications automatically have a higher priority than
        those defined in base applications.

        :param after: Template directory function this template directory
          function to be under. The other template directory has a higher
          priority. You usually want to use ``over``. Optional.
        :param before: Template directory function function this function
          should have priority over. Optional.
        :param name: The name under which to register this template
          directory, so that it can be overridden by applications that
          extend this one.  If no name is supplied a default name is
          generated.

        '''
        global template_directory_id
        self._after = after
        self.before = before
        if name is None:
            name = u'template_directory_%s' % template_directory_id
            template_directory_id += 1
        self.name = name

    def identifier(self, registry):
        return self.name

    def perform(self, obj, registry):
        # XXX hacky to have to get configurable and pass it in
        directory = obj()
        if not os.path.isabs(directory):
            directory = os.path.join(os.path.dirname(
                self.directive.code_info.path), directory)
        registry.register_template_directory_info(
            obj, directory, self.before, self._after,
            self.directive.configurable)


@App.directive('template_loader')
class TemplateLoaderAction(dectate.Action):
    config = DEFAULT_CONFIG

    depends = [TemplateDirectoryAction]

    def __init__(self, extension):
        '''Create a template loader.

        The decorated function gets a ``template_directories`` argument,
        which is a list of absolute paths to directories that contain
        templates. It also gets a ``settings`` argument, which is
        application settings that can be used to configure the loader.

        It should return an object that can load the template
        given the list of template directories.
        '''
        self.extension = extension

    def identifier(self, registry):
        return self.extension

    def perform(self, obj, registry):
        registry.initialize_template_loader(self.extension, obj)


@App.directive('template_render')
class TemplateRenderAction(dectate.Action):
    config = DEFAULT_CONFIG

    depends = [SettingAction, TemplateLoaderAction]

    def __init__(self, extension):
        '''Register a template engine.

        :param extension: the template file extension (``.pt``, etc)
          we want this template engine to handle.

        The decorated function gets ``loader``, ``name`` and
        ``original_render`` arguments. It should return a ``callable``
        that is a view ``render`` function: take a ``content`` and
        ``request`` object and return a :class:`morepath.Response`
        instance. This render callable should render the return value
        of the view with the template supplied through its
        ``template`` argument.
        '''
        self.extension = extension

    def identifier(self, registry):
        return self.extension

    def perform(self, obj, registry):
        registry.register_template_render(self.extension, obj)


@App.directive('view')
class ViewAction(dectate.Action):
    config = DEFAULT_CONFIG

    depends = [SettingAction, PredicateAction,
               TemplateRenderAction]

    def __init__(self, model, render=None, template=None,
                 permission=None,
                 internal=False, **predicates):
        '''Register a view for a model.

        The decorated function gets ``self`` (model instance) and
        ``request`` (:class:`morepath.Request`) parameters. The
        function should return either a (unicode) string that is
        the response body, or a :class:`morepath.Response` object.

        If a specific ``render`` function is given the output of the
        function is passed to this first, and the function could
        return whatever the ``render`` parameter expects as input.
        This function should take the object to render and the
        request.  func:`morepath.render_json` for instance expects as
        its first argument a Python object such as a dict that can be
        serialized to JSON.

        See also :meth:`morepath.App.json` and
        :meth:`morepath.App.html`.

        :param model: the class of the model for which this view is registered.
          The ``self`` passed into the view function is an instance
          of the model (or of a subclass).
        :param render: an optional function that can render the output of the
          view function to a response, and possibly set headers such as
          ``Content-Type``, etc. This function takes ``self`` and
          ``request`` parameters as input.
        :param template: a path to a template file. The path is relative
           to the directory this module is in. The template is applied to
           the content returned from the decorated view function.

           Use the :meth:`morepath.App.template_loader` and
           :meth:`morepath.App.template_render` directives to define
           support for new template engines.
        :param permission: a permission class. The model should have this
          permission, otherwise access to this view is forbidden. If omitted,
          the view function is public.
        :param internal: Whether this view is internal only. If
          ``True``, the view is only useful programmatically using
          :meth:`morepath.Request.view`, but will not be published on
          the web. It will be as if the view is not there.
          By default a view is ``False``, so not internal.
        :param name: the name of the view as it appears in the URL. If omitted,
          it is the empty string, meaning the default view for the model.
          This is a predicate.
        :param request_method: the request method to which this view should
          answer, i.e. GET, POST, etc. If omitted, this view responds to
          GET requests only. This is a predicate.
        :param predicates: additional predicates to match this view
          on. You can install your own using the
          :meth:`morepath.App.predicate` directive.
        '''
        self.model = model
        self.render = render or render_view
        self.template = template
        self.permission = permission
        self.internal = internal
        self.predicates = predicates

    def key_dict(self):
        result = self.predicates.copy()
        result['model'] = self.model
        return result

    def predicate_key(self, registry):
        return registry.key_dict_to_predicate_key(generic.view.wrapped_func,
                                                  self.key_dict())

    def identifier(self, registry):
        return self.predicate_key(registry)

    def perform(self, obj, registry):
        register_view(registry, self.key_dict(), obj,
                      self.render, self.template,
                      self.permission, self.internal)


@App.directive('json')
class JsonAction(ViewAction):
    config = DEFAULT_CONFIG

    group_class = ViewAction

    def __init__(self, model, render=None, template=None, permission=None,
                 internal=False, **predicates):
        """Register JSON view.

        This is like :meth:`morepath.App.view`, but with
        :func:`morepath.render_json` as default for the `render`
        function.

        Transforms the view output to JSON and sets the content type to
        ``application/json``.

        :param model: the class of the model for which this view is registered.
        :param name: the name of the view as it appears in the URL. If omitted,
          it is the empty string, meaning the default view for the model.
        :param render: an optional function that can render the output
          of the view function to a response, and possibly set headers
          such as ``Content-Type``, etc. Renders as JSON by
          default. This function takes ``self`` and
          ``request`` parameters as input.
        :param template: a path to a template file. The path is relative
           to the directory this module is in. The template is applied to
           the content returned from the decorated view function.

           Use the :meth:`morepath.App.template_engine` directive to
           define support for new template engines.
        :param permission: a permission class. The model should have this
          permission, otherwise access to this view is forbidden. If omitted,
          the view function is public.
        :param internal: Whether this view is internal only. If
          ``True``, the view is only useful programmatically using
          :meth:`morepath.Request.view`, but will not be published on
          the web. It will be as if the view is not there.
          By default a view is ``False``, so not internal.
        :param name: the name of the view as it appears in the URL. If omitted,
          it is the empty string, meaning the default view for the model.
          This is a predicate.
        :param request_method: the request method to which this view should
          answer, i.e. GET, POST, etc. If omitted, this view will respond to
          GET requests only. This is a predicate.
        :param predicates: predicates to match this view on. See the
          documentation of :meth:`App.view` for more information.
        """
        render = render or render_json
        super(JsonAction, self).__init__(model, render, template,
                                         permission, internal, **predicates)


@App.directive('html')
class HtmlAction(ViewAction):
    config = DEFAULT_CONFIG

    group_class = ViewAction

    def __init__(self, model, render=None, template=None, permission=None,
                 internal=False, **predicates):
        """Register HTML view.

        This is like :meth:`morepath.App.view`, but with
        :func:`morepath.render_html` as default for the `render`
        function.

        Sets the content type to ``text/html``.

        :param model: the class of the model for which this view is registered.
        :param name: the name of the view as it appears in the URL. If omitted,
          it is the empty string, meaning the default view for the model.
        :param render: an optional function that can render the output
          of the view function to a response, and possibly set headers
          such as ``Content-Type``, etc. Renders as HTML by
          default. This function takes ``self`` and
          ``request`` parameters as input.
        :param template: a path to a template file. The path is relative
           to the directory this module is in. The template is applied to
           the content returned from the decorated view function.

           Use the :meth:`morepath.App.template_engine` directive to
           define support for new template engines.
        :param permission: a permission class. The model should have this
          permission, otherwise access to this view is forbidden. If omitted,
          the view function is public.
        :param internal: Whether this view is internal only. If
          ``True``, the view is only useful programmatically using
          :meth:`morepath.Request.view`, but will not be published on
          the web. It will be as if the view is not there.
          By default a view is ``False``, so not internal.
        :param name: the name of the view as it appears in the URL. If omitted,
          it is the empty string, meaning the default view for the model.
          This is a predicate.
        :param request_method: the request method to which this view should
          answer, i.e. GET, POST, etc. If omitted, this view will respond to
          GET requests only. This is a predicate.
        :param predicates: predicates to match this view on. See the
          documentation of :meth:`App.view` for more information.
        """
        render = render or render_html
        super(HtmlAction, self).__init__(model, render, template,
                                         permission, internal, **predicates)


@App.directive('mount')
class MountAction(PathAction):
    config = DEFAULT_CONFIG

    group_class = PathAction
    depends = [SettingAction, ConverterAction]

    def __init__(self, path, app, variables=None, converters=None,
                 required=None, get_converters=None, name=None):
        """Mount sub application on path.

        The decorated function gets the variables specified in path as
        parameters. It should return a new instance of an application
        class.

        :param path: the path to mount the application on.
        :param app: the :class:`morepath.App` subclass to mount.
        :param variables: a function that given an app instance can construct
          the variables used in the path (including any URL parameters).
          If omitted, variables are retrieved from the app by using
          the arguments of the decorated function.
        :param converters: converters as for the
          :meth:`morepath.App.path` directive.
        :param required: list or set of names of those URL parameters which
          should be required, i.e. if missing a 400 Bad Request response is
          given. Any default value is ignored. Has no effect on path
          variables. Optional.
        :param get_converters: a function that returns a converter dictionary.
          This function is called once during configuration time. It can
          be used to programmatically supply converters. It is merged
          with the ``converters`` dictionary, if supplied. Optional.
        :param name: name of the mount. This name can be used with
          :meth:`Request.child` to allow loose coupling between mounting
          application and mounted application. Optional, and if not supplied
          the ``path`` argument is taken as the name.

        """
        super(MountAction, self).__init__(path,
                                          variables=variables,
                                          converters=converters,
                                          required=required,
                                          get_converters=get_converters)
        self.name = name or path
        self.mounted_app = app

    # XXX what is this for?
    # XXX it's a bit of a hack to make the mount directive
    # group with the path directive so we get conflicts,
    # we need to override prepare to shut it up again
    # def prepare(self, obj):
    #     yield self.clone(), obj

    def discriminators(self, registry):
        return [('mount', self.mounted_app)]

    def perform(self, obj, registry):
        registry.register_mount(
            self.mounted_app, self.path, self.variables,
            self.converters, self.required,
            self.get_converters, self.name, obj)


@App.directive('defer_links')
class DeferLinksAction(dectate.Action):
    config = DEFAULT_CONFIG

    group_class = PathAction
    depends = [SettingAction, MountAction]

    def __init__(self, model):
        """Defer link generation for model to mounted app.

        With ``defer_links`` you can specify that link generation for
        instances of ``model`` is to be handled by a returned mounted
        app if it cannot be handled by the given app
        itself. :meth:`Request.link` and :meth:`Request.view` are
        affected by this directive.

        The decorated function gets an instance of the application and
        object to link to. It should return another application that
        it knows can create links for this object. The function uses
        navigation methods on :class:`App` to do so like
        :meth:`App.parent` and :meth:`App.child`.

        :param model: the class for which we want to defer linking.

        """
        self.model = model

    def identifier(self, registry):
        return ('defer_links', self.model)

    def discriminators(self, registry):
        return [('model', self.model)]

    def perform(self, obj, registry):
        registry.register_defer_links(self.model, obj)


tween_factory_id = 0


@App.directive('tween_factory')
class TweenFactoryAction(dectate.Action):
    config = DEFAULT_CONFIG

    depends = [SettingAction]

    def __init__(self, under=None, over=None, name=None):
        '''Register tween factory.

        The tween system allows the creation of lightweight middleware
        for Morepath that is aware of the request and the application.

        The decorated function is a tween factory. It should return a tween.
        It gets two arguments: the app for which this tween is in use,
        and another tween that this tween can wrap.

        A tween is a function that takes a request and a mounted
        application as arguments.

        Tween factories can be set to be over or under each other to
        control the order in which the produced tweens are wrapped.

        :param under: This tween factory produces a tween that wants to
          be wrapped by the tween produced by the ``under`` tween factory.
          Optional.
        :param over: This tween factory produces a tween that wants to
          wrap the tween produced by the over ``tween`` factory. Optional.
        :param name: The name under which to register this tween factory,
          so that it can be overridden by applications that extend this one.
          If no name is supplied a default name is generated.
        '''
        global tween_factory_id
        self.under = under
        self.over = over
        if name is None:
            name = u'tween_factory_%s' % tween_factory_id
            tween_factory_id += 1
        self.name = name

    def identifier(self, registry):
        return self.name

    def perform(self, obj, registry):
        registry.register_tween_factory(obj, over=self.over, under=self.under)


@App.private_action_class
class IdentityPolicyFunctionAction(dectate.Action):
    """A special action that helps register the identity policy.

    We need this as it needs to be sorted after SettingAction and
    composite actions can't be sorted nor have access to the registry.
    """
    config = DEFAULT_CONFIG
    depends = [SettingAction]

    def __init__(self, dispatch, name):
        self.dispatch = dispatch
        self.name = name

    def identifier(self, registry):
        return (self.dispatch, self.name)

    def perform(self, obj, registry):
        # ugly but it needs to only happen once
        identity_policy = getattr(registry, 'identity_policy', None)
        if identity_policy is None:
            registry.identity_policy = identity_policy = mapply(
                obj,
                settings=registry.settings)
        registry.register_function(
            self.dispatch,
            getattr(identity_policy, self.name))


@App.directive('identity_policy')
class IdentityPolicyAction(dectate.Composite):
    config = DEFAULT_CONFIG

    def __init__(self):
        """Register identity policy.

        The decorated function should return an instance of
        :class:`morepath.security.IdentityPolicy`. Either use an identity
        policy provided by a library or implement your own.

        It gets one optional argument: the settings of the app for which this
        identity policy is in use. So you can pass some settings directly to
        the IdentityPolicy class.
        """
        pass

    def actions(self, obj):
        yield IdentityPolicyFunctionAction(generic.identify,
                                           'identify'), obj
        yield IdentityPolicyFunctionAction(generic.remember_identity,
                                           'remember'), obj
        yield IdentityPolicyFunctionAction(generic.forget_identity,
                                           'forget'), obj



@App.directive('verify_identity')
class VerifyIdentityAction(dectate.Composite):
    def __init__(self, identity=object):
        '''Verify claimed identity.

        The decorated function gives a single ``identity`` argument which
        contains the claimed identity. It should return ``True`` only if the
        identity can be verified with the system.

        This is particularly useful with identity policies such as
        basic authentication and cookie-based authentication where the
        identity information (username/password) is repeatedly sent to
        the the server and needs to be verified.

        For some identity policies (auth tkt, session) this can always
        return ``True`` as the act of establishing the identity means
        the identity is verified.

        The default behavior is to always return ``False``.

        :param identity: identity class to verify. Optional.
        '''
        self.identity = identity

    def actions(self, obj):
        yield FunctionAction(generic.verify_identity,
                             identity=self.identity), obj


@App.directive('dump_json')
class DumpJsonAction(dectate.Action):
    config = DEFAULT_CONFIG

    def __init__(self, model=object):
        '''Register a function that converts model to JSON.

        The decorated function gets ``self`` (model instance) and
        ``request`` (:class:`morepath.Request`) parameters. The
        function should return an JSON object. That is, a Python
        object that can be dumped to a JSON string using
        ``json.dump``.

        :param model: the class of the model for which this function is
          registered. The ``self`` passed into the function is an instance
          of the model (or of a subclass). By default the model is ``object``,
          meaning we register a function for all model classes.
        '''
        self.model = model

    def identifier(self, registry):
        return self.model

    def perform(self, obj, registry):
        # reverse parameters
        def dump(request, self):
            return obj(self, request)
        registry.register_function(generic.dump_json, dump, obj=self.model)


@App.directive('load_json')
class LoadJsonAction(dectate.Action):
    config = DEFAULT_CONFIG

    def __init__(self):
        '''Register a function that converts JSON to an object.

        The decorated function gets ``json`` and ``request``
        (:class:`morepath.Request`) parameters. The function should
        return a Python object based on the given JSON.
        '''
        pass

    def identifier(self, registry):
        return ()

    def perform(self, obj, registry):
        # reverse parameters
        def load(request, json):
            return obj(json, request)
        registry.register_function(generic.load_json, load)


@App.directive('link_prefix')
class LinkPrefixAction(dectate.Action):
    config = DEFAULT_CONFIG

    def __init__(self):
        '''Register a function that returns the prefix added to every link
        generated by the request.

        By default the link generated is based on
        :meth:`webob.Request.application_url`.

        The decorated function gets the ``request`` (:class:`morepath.Request`)
        as its only paremeter. The function should return a string.
        '''
        pass

    def identifier(self, registry):
        return ()

    def perform(self, obj, registry):
        registry.register_function(generic.link_prefix, obj)
