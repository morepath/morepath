"""This module contains the extension API for Morepath. It is useful
when you want to define new directives in a Morepath extension.  An
example an extension that does this is `more.static`_.

.. _`more.static`: https://github.com/morepath/more.static

If you just use Morepath you should not have to import from
:mod:`morepath.directive` in your code. Instead you use the directives
defined in here through :class:`morepath.App`.

Morepath uses the Dectate_ library to implement its directives. The
directives are installed on :class:`morepath.App` using the
:meth:`dectate.App.directive` decorator.

We won't repeat the directive documentation here. If you are
interested in creating a custom directive in a Morepath extension it
pays off to look at the source code of this module. If your custom
directive needs to interact with a core directive you can inherit from
them, and/or refer to them with ``group_class``.

When configuration is committed it is written into various
configuration registries which are attached to the
:attr:`dectate.App.config` class attribute. If you implement your own
directive :class:`dectate.Action` that declares one of these
registries in :attr:`dectate.Action.config` you can import their class
from :mod:`morepath.directive`.

.. _Dectate: http://dectate.readthedocs.org

"""

import os
import dectate
from reg import methodify

from .authentication import Identity, NoIdentity
from .view import render_view, render_json, render_html, ViewRegistry
from .traject import Path
from .converter import ConverterRegistry
from .tween import TweenRegistry
from .template import TemplateEngineRegistry
from .predicate import PredicateRegistry
from .path import PathRegistry
from .settings import SettingRegistry
from .mapply import mapply


def isbaseclass(a, b):
    return issubclass(b, a)


class SettingAction(dectate.Action):
    config = {
        'setting_registry': SettingRegistry
    }

    def __init__(self, section, name):
        """Register application setting.

        An application setting is registered under the
        ``.config.settings_registry`` class attribute of
        :class:`morepath.App` subclasses. It will be executed early
        in configuration so other configuration directives can depend
        on the settings being there.

        The decorated function returns the setting value when executed.

        :param section: the name of the section the setting should go
          under.
        :param name: the name of the setting in its section.
        """
        self.section = section
        self.name = name

    def identifier(self, setting_registry):
        return self.section, self.name

    def perform(self, obj, setting_registry):
        setting_registry.register_setting(self.section, self.name, obj)


class SettingValue(object):
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return self.value


class SettingSectionAction(dectate.Composite):
    query_classes = [SettingAction]

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
class PredicateFallbackAction(dectate.Action):
    config = {
        'predicate_registry': PredicateRegistry
    }

    depends = [SettingAction]

    filter_convert = {
        'dispatch': dectate.convert_dotted_name,
        'func': dectate.convert_dotted_name
    }

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

    def identifier(self, predicate_registry):
        return self.dispatch, self.func

    def perform(self, obj, predicate_registry):
        predicate_registry.register_predicate_fallback(
            self.dispatch, self.func, obj)


class PredicateAction(dectate.Action):
    config = {
        'predicate_registry': PredicateRegistry
    }

    depends = [SettingAction, PredicateFallbackAction]

    filter_convert = {
        'dispatch': dectate.convert_dotted_name,
        'index': dectate.convert_dotted_name,
        'before': dectate.convert_dotted_name,
        'after': dectate.convert_dotted_name,
    }

    filter_name = {
        'before': '_before',
        'after': '_after'
    }

    def __init__(self, dispatch, name, default, index,
                 before=None, after=None):
        """Register custom predicate for a predicate_dispatch function.

        The function registered should have arguments that are the
        same as the arguments of the :reg:`reg.predicate_dispatch`
        function. From these arguments it should determine a predicate
        value and return it. The predicates for a ``predicate_dispatch``
        function are ordered by their before and after arguments.

        You can then register a function to dispatch to using the
        :meth:`App.method` directive. This takes the
        ``predicate_dispatch`` or ``dispatch`` function as its first
        argument and the predicate key to match on as its other
        arguments.

        :param dispatch: the dispatch function this predicate
           is for.
        :param name: the name of the predicate. This is used when
          constructing a predicate key from a predicate dictionary.
        :param default: the default value for a predicate, in case the
          value is missing in the predicate dictionary.
        :param index: the index to use. Typically :class:`reg.KeyIndex` or
          :class:`reg.ClassIndex`.
        :param before: predicate function this function wants to have
           priority over.
        :param after: predicate function we want to have priority over
           this one.
        """
        self.dispatch = dispatch
        self.name = name
        self.default = default
        self.index = index
        self._before = before
        self._after = after

    def identifier(self, predicate_registry):
        return self.dispatch, self._before, self._after

    def perform(self, obj, predicate_registry):
        predicate_registry.register_predicate(
            obj, self.dispatch,
            self.name, self.default, self.index,
            self._before, self._after)

    @staticmethod
    def after(predicate_registry):
        predicate_registry.install_predicates()


class MethodAction(dectate.Action):
    config = {
    }

    depends = [SettingAction,
               PredicateAction, PredicateFallbackAction]

    def filter_get_value(self, name):
        return self.key_dict.get(name, dectate.NOT_FOUND)

    app_class_arg = True

    # XXX we cannot search for non-string kw as we cannot define
    # the convert
    filter_convert = {
        'dispatch_method': dectate.convert_dotted_name
    }

    def __init__(self, dispatch_method, **kw):
        '''Register function as implementation of dispatch method.

        This way you can create new hookable functions of your own, or
        override parts of the Morepath framework itself.

        The ``dispatch_method`` argument is a dispatch method, so a
        method on a :class:`morepath.App`` class marked with
        :func:`reg.dispatch_method`, so for instance ``App.foo``. The
        registered function gets the instance of this app class as its
        first argument. The registered function must have the same arguments
        as the arguments of the dispatch function.

        The reason to use this form of registration instead of
        :meth:`reg.Dispatch.register` directly is so that they are
        overridable just like any other Morepath directive.

        :param dispatch_method: the dispatch method to register an
          implementation for.
        :param kw: keyword parameters with the predicate keys to
           register for.  Argument names are predicate names, values
           are the predicate values to match on. These are like
           the predicate arguments for :meth:`reg.Dispatch.register`.
        '''
        self.dispatch_method = dispatch_method
        self.key_dict = kw

    def identifier(self, app_class):
        return (self.dispatch_method,
                self.dispatch_method.key_dict_to_predicate_key(self.key_dict))

    def perform(self, obj, app_class):
        getattr(app_class, self.dispatch_method.__name__).register(
            obj, **self.key_dict)


class ConverterAction(dectate.Action):
    config = {
        'converter_registry': ConverterRegistry
    }

    depends = [SettingAction]

    # use __builtin__.foo to match with builtin foo
    filter_convert = {
        'type': dectate.convert_dotted_name
    }

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

    def identifier(self, converter_registry):
        return ('converter', self.type)

    def perform(self, obj, converter_registry):
        converter_registry.register_converter(self.type, obj())


class PathAction(dectate.Action):
    config = {
        'path_registry': PathRegistry,
    }

    depends = [SettingAction, ConverterAction]

    filter_compare = {
        'model': isbaseclass,
        'path': lambda a, b: Path(a).discriminator() == Path(b).discriminator()
    }

    def __init__(self, path, model=None,
                 variables=None, converters=None, required=None,
                 get_converters=None, absorb=False):
        self.model = model
        self.path = path
        self.variables = variables
        self.converters = converters
        self.required = required
        self.get_converters = get_converters
        self.absorb = absorb

    def identifier(self, path_registry):
        return ('path', Path(self.path).discriminator())

    def discriminators(self, path_registry):
        return [('model', self.model)]

    def perform(self, obj, path_registry):
        path_registry.register_path(
            self.model, self.path,
            self.variables, self.converters, self.required,
            self.get_converters, self.absorb,
            obj)


class PathCompositeAction(dectate.Composite):
    filter_convert = {
        'model': dectate.convert_dotted_name,
        'variables': dectate.convert_dotted_name,
        'get_converters': dectate.convert_dotted_name,
        'absorb': dectate.convert_bool,
    }

    query_classes = [PathAction]

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
        :param variables: a function takes ``app`` and ``model
          object`` arguments. The ``app`` argument is optional.  It
          can construct the variables used in the path (including any
          URL parameters). If ``variables`` is omitted, variables are
          retrieved from the model by using the arguments of the
          decorated function.
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
          function as the ``absorb`` argument.

        """
        self.model = model
        self.path = path
        self.variables = variables
        self.converters = converters
        self.required = required
        self.get_converters = get_converters
        self.absorb = absorb

    def actions(self, obj):
        # this composite action exists to let you use path with a
        # class and still have the path action discriminator work
        # correctly, which reports a conflict if you use the path
        # action with the same model multiple times.
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
        yield PathAction(self.path, model, self.variables, self.converters,
                         self.required, self.get_converters, self.absorb), obj


class PermissionRuleAction(dectate.Action):
    config = {
    }

    filter_convert = {
        'model': dectate.convert_dotted_name,
        'permission': dectate.convert_dotted_name,
        'identity': dectate.convert_dotted_name,
    }

    filter_compare = {
        'model': isbaseclass,
        'permission': issubclass,
        'identity': issubclass
    }

    app_class_arg = True

    depends = [SettingAction]

    def __init__(self, model, permission, identity=Identity):
        """Declare whether a model has a permission.

        The decorated function receives ``app``, ``model``,
        `permission`` (instance of any permission object) and
        ``identity`` (:class:`morepath.Identity`) parameters. The
        ``app`` argument is optional. The decorated function should
        return ``True`` only if the given identity exists and has that
        permission on the model.

        :param model: the model class
        :param permission: permission class
        :param identity: identity class to check permission for. If ``None``,
          the identity to check for is the special
          :data:`morepath.NO_IDENTITY`.

        """
        self.model = model
        self.permission = permission
        if identity is None:
            identity = NoIdentity
        self.identity = identity

    def identifier(self, app_class):
        return (self.model, self.permission, self.identity)

    def perform(self, obj, app_class):
        app_class._permits.register(
            methodify(obj, selfname='app'),
            identity=self.identity,
            obj=self.model,
            permission=self.permission)


template_directory_id = 0


class TemplateDirectoryAction(dectate.Action):
    config = {
        'template_engine_registry': TemplateEngineRegistry
    }

    depends = [SettingAction]

    filter_name = {
        'after': '_after',
        'before': '_before'
    }

    filter_convert = {
        'after': dectate.convert_dotted_name,
        'before': dectate.convert_dotted_name,
    }

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
        self._before = before
        if name is None:
            name = u'template_directory_%s' % template_directory_id
            template_directory_id += 1
        self.name = name

    def identifier(self, template_engine_registry):
        return self.name

    def perform(self, obj, template_engine_registry):
        directory = obj()
        if not os.path.isabs(directory):
            directory = os.path.join(os.path.dirname(
                self.code_info.path), directory)
        # hacky to have to get configurable and pass it in.
        # note that this cannot be app_class as we want the app of
        # the directive that *defined* it so we sort things properly.
        template_engine_registry.register_template_directory_info(
            obj, directory, self._before, self._after,
            self.directive.configurable)


class TemplateLoaderAction(dectate.Action):
    config = {
        'template_engine_registry': TemplateEngineRegistry
    }

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

    def identifier(self, template_engine_registry):
        return self.extension

    def perform(self, obj, template_engine_registry):
        template_engine_registry.initialize_template_loader(
            self.extension, obj)


class TemplateRenderAction(dectate.Action):
    config = {
        'template_engine_registry': TemplateEngineRegistry
    }

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

    def identifier(self, template_engine_registry):
        return self.extension

    def perform(self, obj, template_engine_registry):
        template_engine_registry.register_template_render(self.extension, obj)


def issubclass_or_none(a, b):
    if a is None or b is None:
        return a == b
    return issubclass(a, b)


def isbaseclass_notfound(a, b):
    # NOT_FOUND can happen in case of a fallback
    if a is dectate.NOT_FOUND:
        a = object
    return isbaseclass(a, b)


class ViewAction(dectate.Action):
    config = {
        'view_registry': ViewRegistry,
    }

    depends = [SettingAction, PredicateAction,
               TemplateRenderAction]

    filter_convert = {
        'model': dectate.convert_dotted_name,
        'render': dectate.convert_dotted_name,
        'permission': dectate.convert_dotted_name,
        'internal': dectate.convert_bool,
        'body_model': dectate.convert_dotted_name,
    }

    def filter_get_value(self, name):
        return self.predicates.get(name, dectate.NOT_FOUND)

    filter_compare = {
        'model': isbaseclass,
        'permission': issubclass_or_none,
        'body_model': isbaseclass_notfound,
    }

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

    def identifier(self, view_registry):
        return view_registry.predicate_key(self.key_dict())

    def perform(self, obj, view_registry):
        view_registry.register_view(
            self.key_dict(), obj,
            self.render, self.template,
            self.permission, self.internal)


class JsonAction(ViewAction):
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


class HtmlAction(ViewAction):
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


# used by Mount to make sure there's at least a model to filter in a query
class DummyModel(object):
    pass


class MountAction(PathAction):
    group_class = PathAction
    depends = [SettingAction, ConverterAction]

    filter_convert = {
        'app': dectate.convert_dotted_name
    }
    filter_convert.update(PathCompositeAction.filter_convert)

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
                                          model=DummyModel,
                                          variables=variables,
                                          converters=converters,
                                          required=required,
                                          get_converters=get_converters)
        self.name = name or path
        self.app = app

    def discriminators(self, path_registry):
        return [('mount', self.app)]

    def perform(self, obj, path_registry):
        path_registry.register_mount(
            self.app, self.path, self.variables,
            self.converters, self.required,
            self.get_converters, self.name, obj)


class DeferLinksAction(dectate.Action):
    group_class = PathAction
    depends = [SettingAction, MountAction]

    filter_convert = PathCompositeAction.filter_convert

    filter_compare = {
        'model': isbaseclass
    }

    def __init__(self, model):
        """Defer link generation for model to mounted app.

        With ``defer_links`` you can specify that link generation for
        instances of ``model`` is to be handled by a returned mounted
        app if it cannot be handled by the given app
        itself. :meth:`Request.link` and :meth:`Request.view` are
        affected by this directive. Note that
        :meth:`Request.class_link` is **not** affected by this
        directive, but you can use
        :meth:`morepath.App.defer_class_links` instead.

        The decorated function gets an instance of the application and
        object to link to. It should return another application that
        it knows can create links for this object. The function uses
        navigation methods on :class:`App` to do so like
        :meth:`App.parent` and :meth:`App.child`.

        :param model: the class for which we want to defer linking.

        """
        self.model = model

    def identifier(self, path_registry):
        return ('defer_links', self.model)

    def discriminators(self, path_registry):
        return [('model', self.model)]

    def perform(self, obj, path_registry):
        path_registry.register_defer_links(self.model, obj)


class DeferClassLinksAction(dectate.Action):
    group_class = PathAction
    depends = [SettingAction, MountAction]

    filter_convert = PathCompositeAction.filter_convert

    filter_compare = {
        'model': isbaseclass
    }

    def __init__(self, model, variables):
        """Defer class link generation for model class to mounted app.

        With ``defer_class_links`` you can specify that link
        generation for model classes is to be handled by a returned
        mounted app if it cannot be handled by the given app
        itself. :meth:`Request.class_link`, :meth:`Request.link` and
        :meth:`Request.view` are affected by this directive.

        The decorated function gets an instance of the application,
        the model class and a variables dict. It should return another
        application that it knows can create links for this class. The
        function uses navigation methods on :class:`App` to do so like
        :meth:`App.parent` and :meth:`App.child`.

        You also have to supply a ``variables`` argument to describe
        how to get the variables from an instance -- this should be
        return the same variables as needed by the ``path`` directive
        in the app you are deferring to. This allows
        ``defer_class_links`` to function as ``defer_links`` for model
        objects as well.

        :param model: the class for which we want to defer linking.
        :param variables: a function that given a model object can
          construct the variables used in the path (including any URL
          parameters).

        """
        self.model = model
        self.variables = variables

    def identifier(self, path_registry):
        # either implement defer_links for a model or implement
        # defer_class_links but not both
        return ('defer_links', self.model)

    def discriminators(self, path_registry):
        return [('model', self.model)]

    def perform(self, obj, path_registry):
        path_registry.register_defer_class_links(
            self.model, self.variables, obj)


tween_factory_id = 0


class TweenFactoryAction(dectate.Action):
    config = {
        'tween_registry': TweenRegistry
    }

    depends = [SettingAction]

    filter_convert = {
        'under': dectate.convert_dotted_name,
        'over': dectate.convert_dotted_name,
    }

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

    def identifier(self, tween_registry):
        return self.name

    def perform(self, obj, tween_registry):
        tween_registry.register_tween_factory(
            obj, over=self.over, under=self.under)


class IdentityPolicyAction(dectate.Action):
    depends = [SettingAction]

    config = {
        'setting_registry': SettingRegistry,
    }

    app_class_arg = True

    def __init__(self):
        """Register identity policy.

        The decorated function should return an instance of
        :class:`morepath.IdentityPolicy`. Either use an identity
        policy provided by a library or implement your own.

        It gets one optional argument: the settings of the app for which this
        identity policy is in use. So you can pass some settings directly to
        the IdentityPolicy class.
        """
        pass

    def identifier(self, setting_registry, app_class):
        return ()

    def perform(self, obj, setting_registry, app_class):
        identity_policy = mapply(
            obj, settings=setting_registry)
        app_class._identify = identity_policy.identify
        app_class.remember_identity = identity_policy.remember
        app_class.forget_identity = identity_policy.forget


class VerifyIdentityAction(dectate.Action):
    depends = [SettingAction]

    config = {
    }

    app_class_arg = True

    filter_convert = {
        'identity': dectate.convert_dotted_name,
    }

    def __init__(self, identity=object):
        '''Verify claimed identity.

        The decorated function takes an ``app`` argument and an
        ``identity`` argument which contains the claimed identity. The
        ``app`` argument is optional. It should return ``True`` only
        if the identity can be verified with the system.

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

    def identifier(self, app_class):
        return self.identity

    def perform(self, obj, app_class):
        app_class._verify_identity.register(
            methodify(obj, selfname='app'),
            identity=self.identity)


class DumpJsonAction(dectate.Action):
    config = {
    }

    filter_convert = {
        'model': dectate.convert_dotted_name
    }

    filter_compare = {
        'model': isbaseclass
    }

    app_class_arg = True

    def __init__(self, model=object):
        '''Register a function that converts model to JSON.

        The decorated function gets ``app`` (app instance), ``obj``
        (model instance) and ``request`` (:class:`morepath.Request`)
        arguments. The ``app`` argument is optional. The function
        should return an JSON object. That is, a Python object that
        can be dumped to a JSON string using ``json.dump``.

        :param model: the class of the model for which this function is
          registered. The ``self`` passed into the function is an instance
          of the model (or of a subclass). By default the model is ``object``,
          meaning we register a function for all model classes.
        '''
        self.model = model

    def identifier(self, app_class):
        return self.model

    def perform(self, obj, app_class):
        app_class._dump_json.register(
            methodify(obj, selfname='app'),
            obj=self.model)


class LoadJsonAction(dectate.Action):
    config = {
    }

    app_class_arg = True

    def __init__(self):
        '''Register a function that converts JSON to an object.

        The decorated function gets ``app``, ``json`` and ``request``
        (:class:`morepath.Request`) arguments. The ``app`` argument is
        optional. The function should return a Python object based on
        the given JSON.
        '''
        pass

    def identifier(self, app_class):
        return ()

    def perform(self, obj, app_class):
        app_class._load_json = methodify(obj, selfname='app')


class LinkPrefixAction(dectate.Action):
    config = {
    }

    app_class_arg = True

    def __init__(self):
        '''Register a function that returns the prefix added to every link
        generated by the request.

        By default the link generated is based on
        :meth:`webob.Request.application_url`.

        The decorated function gets ``app`` and ``request``
        (:class:`morepath.Request`) arguments. The ``app`` argument is
        optional. The function should return a string.
        '''
        pass

    def identifier(self, app_class):
        return ()

    def perform(self, obj, app_class):
        app_class._link_prefix = methodify(obj, selfname='app')
