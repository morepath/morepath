from webob.exc import HTTPNotFound
from reg import mapply

from .app import App
from .traject import create_path
from . import generic


DEFAULT_NAME = u''


class ResponseSentinel(object):
    pass


RESPONSE_SENTINEL = ResponseSentinel()


def resolve_model(request):
    """Resolve path to a obj.
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
    # cannot find obj or app
    return None


def resolve_response(request, obj):
    request.view_name = get_view_name(request.unconsumed)
    view = generic.view.component(request, obj, lookup=request.lookup)
    if view is None:
        # try to look up fallback and use it
        fallback = generic.view.fallback(request, obj, lookup=request.lookup)
        # the default fallback is not found
        if fallback is None:
            return HTTPNotFound()
        return fallback(request, obj)
    return view.response(request, obj)


def get_view_name(stack):
    unconsumed_amount = len(stack)
    if unconsumed_amount > 1:
        raise HTTPNotFound()
    elif unconsumed_amount == 0:
        return DEFAULT_NAME
    elif unconsumed_amount == 1:
        return stack[0].lstrip('+')
    assert False, ("Unconsumed stack: %s" %
                   create_path(stack))  # pragma: nocoverage


def publish(request):
    model = resolve_model(request)
    return resolve_response(request, model)


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
