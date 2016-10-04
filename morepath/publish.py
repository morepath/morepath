"""
Functionality to turn a :class:`morepath.Request` into a
:class:`morepath.Response` using Morepath configuration. It looks up a
model instance for the request path and parameters, then looks up a
view for that model object to create the response.

The publish module:

* resolves the request into a model object.

* resolves the model object and the request into a view.

* the view then generates a response.

It all starts at :func:`publish`.
"""

from webob.exc import HTTPNotFound

from .app import App


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
    :attr:`morepath.Request.unconsumed` and consumes it step by step
    using :func:`morepath.TrajectRegistry.consume` to find the model
    object as declared by :meth:`morepath.App.path` directive. It can
    traverse through mounted applications as indicated by the
    :meth:`morepath.App.mount` directive.

    :param: :class:`morepath.Request` instance.
    :return: model object or ``None`` if not found.
    """
    app = request.app
    while request.unconsumed:
        next = app.config.path_registry.consume(request)
        if next is None:
            # we cannot find the next object
            # this may be cause there was no matching route
            # or because the model factory returned None
            return next
        # we found a non-app instance, return it
        if not isinstance(next, App):
            return next
        # we found an app, make it the current app
        next.parent = app
        request.app = next
        app = next
    # we have an app and we don't have anything to consume,
    # so consume to root
    return app.config.path_registry.consume(request)


def resolve_response(obj, request):
    """Given model object and request, create response.

    This uses :func:`get_view_name` to set up the view name on the
    request object.

    If no view name exist it raises :exc:`webob.exc.HTTPNotFound`.

    It then uses :meth:`morepath.App.get_view` to resolve the view for
    the model object and the request by doing dynamic dispatch.

    :param obj: model object to get response for.
    :param request: :class:`morepath.Request` instance.
    :return: :class:`morepath.Response` instance

    """
    view_name = request.view_name = get_view_name(request.unconsumed)
    if view_name is None:
        raise HTTPNotFound()
    return request.app.get_view(obj, request)


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
