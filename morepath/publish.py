from .error import ModelError
from morepath import generic
from .traject import parse_path, create_path
from werkzeug.exceptions import HTTPException, NotFound


DEFAULT_NAME = u''


class ResponseSentinel(object):
    pass


RESPONSE_SENTINEL = ResponseSentinel()

# XXX want to make some of these generic functions?

# XXX do we need to use all to look up consumers?

# XXX find a better place for this kind of API doc. perhaps revise
# the way .all works as a keyword argument to function call?
# a consumer consumes steps in a stack to find an object.
# a consumer function has this signature:
# def consumer(obj, stack, lookup):
#         """Consumes steps.
#         Returns a boolean meaning that some stack has been consumed,
#         an object and the rest of unconsumed stack
#         """

class Mount(object):
    def __init__(self, app):
        self.app = app

def resolve_model(request, app):
    """Resolve path to a model using consumers.
    """
    unconsumed = parse_path(request.path)
    lookup = request.lookup # XXX can get this from argument too
    obj = app
    # if there is no stack, we consume toward a root model
    if not unconsumed:
        for consumer in generic.consumer.all(obj, lookup=lookup):
            any_consumed, obj, unconsumed = consumer(obj, unconsumed, lookup)
            if any_consumed:
                break
        request.unconsumed = unconsumed
        return obj
    # consume steps toward model
    mounts = request.mounts
    mounts.append(Mount(app))
    while unconsumed:
        for consumer in generic.consumer.all(obj, lookup=lookup):
            any_consumed, obj, unconsumed = consumer(
                obj, unconsumed, lookup)
            if any_consumed:
                if isinstance(obj, Mount):
                    mounts.append(obj)
                # get new lookup for whatever we found if it exists
                lookup = generic.lookup(obj, lookup=lookup, default=lookup)
                break
        else:
            # nothing could be consumed
            break
    request.lookup = lookup
    request.unconsumed = unconsumed
    return obj


def resolve_response(request, model):
    name = get_view_step(model, request.unconsumed)

    request.set_resolver_info({'name': name})

    response = generic.response(request, model, default=RESPONSE_SENTINEL,
                                lookup=request.lookup)
    if response is RESPONSE_SENTINEL:
        # XXX lookup error view and fallback to default
        raise NotFound()
    return response


def get_view_step(model, stack):
    unconsumed_amount = len(stack)
    if unconsumed_amount == 0:
        return DEFAULT_NAME
    elif unconsumed_amount == 1:
        return stack[0].lstrip('+')
    raise ModelError(
        "%r has unresolved path %s" % (model, create_path(stack)))


def publish(request, app):
    model = resolve_model(request, app)
    try:
        return resolve_response(request, model)
    except HTTPException as e:
        return e.get_response(request.environ)
