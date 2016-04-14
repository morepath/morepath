from webob.exc import HTTPNotFound
from reg import mapply

from .app import App
from . import generic


DEFAULT_NAME = u''


def publish(request):
    """Handle request and return response.

    It uses :func:`resolve_model` to use the information in
    ``request`` (path, request method, etc) to resolve to a model
    object. :func:`resolve_response` then creates a view for
    the request and the object.

    :param request: :class:`morepath.Request` instance.
    :param return: :class:`morepath.Response` instance.

    """
    obj = resolve_model(request)
    return resolve_response(obj, request)


def resolve_model(request):
    """Resolve request to a model object.

    This takes the path information as a stack of path segments in
    :attr:`morepath.Request.unconsumed` and consumes it step by step using
    :func:`consume` to find the model object as declared by
    :meth:`morepath.App.path` directive. It can traverse through
    mounted applications as indicated by the
    :meth:`morepath.App.mount` directive.

    :param: :class:`morepath.Request` instance.
    :return: model object or ``None`` if not found.
    """
    app = request.app
    app.set_implicit()
    while request.unconsumed:
        next = consume(request, app)
        if next is None:
            # cannot find next obj or app
            break
        # we found a non-app instance, return it
        if not isinstance(next, App):
            return next
        # we found an app, make it the current app
        next.set_implicit()
        next.parent = app
        request.app = next
        request.lookup = next.lookup
        app = next
    # if there is nothing (left), we consume toward a root obj
    if not request.unconsumed:
        return consume(request, app)
    # cannot find obj
    return None


def resolve_response(obj, request):
    """Given model object and request, create response.

    This uses :func:`get_view_name` to set up the view name on the
    request object.

    If no view name exist it raises :exc:`webob.exc.HTTPNotFound`.

    It then uses :func:`morepath.generic.view` to resolve the view for
    the model object and the request by doing dynamic dispatch.

    :param obj: model object to get response for.
    :param request: :class:`morepath.Request` instance.
    :return: :class:`morepath.Response` instance

    """
    view_name = request.view_name = get_view_name(request.unconsumed)
    if view_name is None:
        raise HTTPNotFound()
    return generic.view(obj, request, lookup=request.lookup)


def get_view_name(stack):
    """Determine view name from leftover stack of path segments

    :param stack: a list of path segments left over after consuming
      the path.
    :return: view name string or ``None`` if no view name can be determined.
    """
    unconsumed_amount = len(stack)
    if unconsumed_amount == 0:
        # no special view segments means use default view name
        return DEFAULT_NAME
    elif unconsumed_amount == 1:
        # last segment is view name, strip off any ``+`` view marker.
        return stack[0].lstrip('+')
    else:
        # more than one segments means we have a path that doesn't exist
        return None


def consume(request, app):
    """Consume request.unconsumed to new obj, starting with app.

    Returns the new model instance, or None if no new instance could be found.
    The model instance may be an app instance.

    Adjusts request.unconsumed with the remaining unconsumed stack.
    """
    value, stack, traject_variables = app.config.path_registry.consume(
        request.unconsumed)
    if value is None:
        return None
    get_obj, get_parameters = value
    variables = get_parameters(request.GET)
    variables['request'] = request
    variables['app'] = app
    variables.update(traject_variables)
    next_obj = mapply(get_obj, **variables)
    if next_obj is None:
        return None
    request.unconsumed = stack
    return next_obj
