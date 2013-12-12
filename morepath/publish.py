from morepath import generic
from .model import Mount
from .traject import parse_path, create_path
from werkzeug.exceptions import HTTPException, NotFound


DEFAULT_NAME = u''


class ResponseSentinel(object):
    pass


RESPONSE_SENTINEL = ResponseSentinel()


def resolve_model(request, mount):
    """Resolve path to a model using consumers.
    """
    unconsumed = parse_path(request.path)
    lookup = request.lookup  # XXX can get this from argument too
    # consume steps toward model
    mounts = request.mounts
    obj = mount
    mounts.append(obj)
    while unconsumed:
        any_consumed, obj, unconsumed = generic.consume(obj,
                                                        unconsumed=unconsumed,
                                                        lookup=lookup)
        if not any_consumed:
            break
        if isinstance(obj, Mount):
            mounts.append(obj)
        # get new lookup for whatever we found if it exists
        lookup = generic.lookup(obj, lookup=lookup, default=lookup)
    # if there is no stack, we consume toward a root model
    if not unconsumed:
        any_consumed, obj, unconsumed = generic.consume(obj,
                                                        unconsumed=unconsumed,
                                                        lookup=lookup)
    request.lookup = lookup
    request.unconsumed = unconsumed
    return obj


def resolve_response(request, model):
    request.view_name = get_view_name(request.unconsumed)

    response = generic.response(request, model, default=RESPONSE_SENTINEL,
                                lookup=request.lookup)
    if response is RESPONSE_SENTINEL:
        # XXX lookup error view and fallback to default
        raise NotFound()
    return response


def get_view_name(stack):
    unconsumed_amount = len(stack)
    if unconsumed_amount > 1:
        raise NotFound()
    elif unconsumed_amount == 0:
        return DEFAULT_NAME
    elif unconsumed_amount == 1:
        return stack[0].lstrip('+')
    assert False, "Unconsumed stack: %s" % create_path(stack)


def publish(request, mount):
    model = resolve_model(request, mount)
    try:
        return resolve_response(request, model)
    except HTTPException as e:
        return e.get_response(request.environ)
