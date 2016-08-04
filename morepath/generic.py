"""These generic functions are by Morepath's implementation (response
generation, link generation, authentication, json load/restore).

The functions are made pluggable by the use of the
:func:`reg.dispatch` and :func:`reg.dispatch_external_predicates`
decorators. Morepath's configuration function uses this to register
implementations using :meth:`reg.Registry.register_function`.

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


@reg.dispatch('obj')
def dump_json(request, obj):
    """Dump an object as JSON.

    ``obj`` is any Python object, try to interpret it as JSON.

    :param request: :class:`morepath.Request`
    :param obj: any Python object to convert to JSON.
    :return: JSON representation (in Python form).
    """
    return obj
