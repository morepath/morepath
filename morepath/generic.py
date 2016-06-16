"""These generic functions are by Morepath's implementation (response
generation, link generation, authentication, json load/restore).

The functions are made pluggable by the use of the
:func:`reg.dispatch` and :func:`reg.dispatch_external_predicates`
decorators. Morepath's configuration function uses this to register
implementations using :meth:`reg.Registry.register_function`.

:func:`morepath.remember_identity`, :func:`morepath.forget_identity`
and :func:`morepath.settings`, currently exported to the public API,
are now deprecated.

"""
import reg
from webob.exc import HTTPNotFound


@reg.dispatch(reg.match_class('model', lambda model: model))
def class_path(model, variables):
    """Get the path for a model class.

    :param model: model class or :class:`morepath.App` subclass.
    :param variables: dictionary with variables to reconstruct
      the path and URL paramaters from path pattern.
    :return: a tuple with URL path and URL parameters, or ``None`` if
      path cannot be determined.
    """
    return None


@reg.dispatch('obj')
def path_variables(obj, lookup):
    """Get variables to use in path generation.

    :param obj: model object or :class:`morepath.App` instance.
    :return: a dict with the variables to use for constructing the path,
      or ``None`` if no such dict can be found.
    """
    return default_path_variables(obj, lookup=lookup)


@reg.dispatch('obj')
def default_path_variables(obj):
    """Get default variables to use in path generation.

    Invoked if no specific ``path_variables`` is registered.

    :param obj: model object for ::class:`morepath.App` instance.
    :return: a dict with the variables to use for constructing the path, or
      ``None`` if no such dict can be found.
    """
    return None


@reg.dispatch('obj')
def deferred_link_app(mounted, obj):
    """Get application used for link generation.

    :param mounted: current :class:`morepath.App` instance.
    :param obj: model object to link to.
    :return: instance of :class:`morepath.App` subclass that handles
      link generation for this model, or ``None`` if no app exists
      that can construct link.
    """
    return None


@reg.dispatch(reg.match_class('model', lambda model: model))
def deferred_class_link_app(mounted, model, variables):
    """Get application used for link generation for a model class.

    :param mounted: current :class:`morepath.App` instance.
    :param model: model class
    :param variables: dict of variables used to construct class link
    :return: instance of :class:`morepath.App` subclass that handles
      link generation for this model class, or ``None`` if no app exists
      that can construct link.
    """
    return None


@reg.dispatch_external_predicates()
def view(obj, request):
    """Get the view that represents the obj in the context of a request.

    This view is a representation of the obj that can be rendered to a
    response. It may also return a :class:`morepath.Response`
    directly.

    Predicates are installed in :mod:`morepath.core` that inspect both
    ``obj`` and ``request`` to see whether a matching view can be found.

    :param obj: model object to represent with view.
    :param request: :class:`morepath.Request` instance.
    :return: :class:`morepath.Response` object, or
      :class:`webob.exc.HTTPNotFound` if view cannot be found.
    """
    return HTTPNotFound()


@reg.dispatch()
def settings():
    """Return current settings object.

    In it are sections, and inside of the sections are the setting values.
    If there is a ``logging`` section and a ``loglevel`` setting in it,
    this is how you would access it::

      settings().logging.loglevel

    **Deprecated**: use the property :attr:`morepath.App.settings` instead.

    :return: current settings object for this app.
    """
    raise NotImplementedError  # pragma: nocoverage


@reg.dispatch()
def identify(request):
    """Determine identity for request.

    :param: a :class:`morepath.Request` instance.
    :return: a :class:`morepath.Identity` instance or ``None`` if
      no identity can be found. Can also return :data:`morepath.NO_IDENTITY`,
      but ``None`` is converted automatically to this.
    """
    return None


@reg.dispatch('identity')
def verify_identity(identity):
    """Returns True if the claimed identity can be verified.

    Look in the database to verify the identity, or in case of auth
    tokens, always consider known identities to be correct.

    :param: :class:`morepath.Identity` instance.
    :return: ``True`` if identity can be verified. By default no identity
      can be verified so this returns ``False``.
    """
    return False


@reg.dispatch()
def remember_identity(response, request, identity):
    """Modify response so that identity is remembered by client.

    **Deprecated**: use the method
    :meth:`morepath.App.remember_identity` instead.

    :param response: :class:`morepath.Response` to remember identity on.
    :param request: :class:`morepath.Request`
    :param identity: :class:`morepath.Identity`

    """
    raise NotImplementedError  # pragma: nocoverage


@reg.dispatch()
def forget_identity(response, request):
    """Modify response so that identity is forgotten by client.

    **Deprecated**: use the method
    :meth:`morepath.App.forget_identity` instead.

    :param response: :class:`morepath.Response` to forget identity on.
    :param request: :class:`morepath.Request`
    """
    raise NotImplementedError  # pragma: nocoverage


@reg.dispatch('identity', 'obj',
              reg.match_class('permission',
                              lambda permission: permission))
def permits(identity, obj, permission):
    """Returns ``True`` if identity has permission for model object.

    identity can be the special :data:`morepath.NO_IDENTITY`
    singleton; register for :class:`morepath.NoIdentity` to handle
    this case separately.

    :param identity: :class:`morepath.Identity`
    :param obj: model object
    :param permission: permission class.
    :return: ``True`` if identity has permission for obj.
    """
    return False


@reg.dispatch()
def load_json(request, json):
    """Load JSON as some object.

    By default JSON is loaded as itself.

    :param request: :class:`morepath.Request`
    :param json: JSON (in Python form) to convert into object.
    :return: Any Python object, including JSON.
    """
    return json


@reg.dispatch('obj')
def dump_json(request, obj):
    """Dump an object as JSON.

    ``obj`` is any Python object, try to interpret it as JSON.

    :param request: :class:`morepath.Request`
    :param obj: any Python object to convert to JSON.
    :return: JSON representation (in Python form).
    """
    return obj


@reg.dispatch()
def link_prefix(request):
    """Returns a prefix that's added to every link generated by the request.

    By default :attr:`webob.request.BaseRequest.application_url` is used.

    :param request: :class:`morepath.Request`
    :return: prefix string to add before links.
    """
    return request.application_url
