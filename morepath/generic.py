"""These generic functions are by Morepath's implementation (response
generation, link generation, authentication, json load/restore).

The functions are made pluggable by the use of the
:func:`reg.dispatch` and :func:`reg.dispatch_external_predicates`
decorators. Morepath's configuration function uses this to register
implementations using :meth:`reg.Registry.register_function`.

"""
import reg
from webob.exc import HTTPNotFound


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
