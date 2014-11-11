from morepath import generic
from .app import App
from .traject import create_path
from webob.exc import HTTPNotFound


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
        next = generic.consume(request, app, lookup=app.lookup)
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
        return generic.consume(request, app, lookup=app.lookup)
    # cannot find obj or app
    return None


def resolve_response(request, model):
    request.view_name = get_view_name(request.unconsumed)
    response = generic.response(request, model, lookup=request.lookup)
    if response is None:
        raise HTTPNotFound()
    return response


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
