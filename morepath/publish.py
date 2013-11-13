from .error import ModelError
from morepath import generic
from .traject import parse_path, create_path
from werkzeug.exceptions import HTTPException, NotFound


DEFAULT_NAME = u''


class ResponseSentinel(object):
    pass


RESPONSE_SENTINEL = ResponseSentinel()


# XXX
# want to rethink this module in terms of generic functions.
# we could introduce a generic.model, generic.response could
# gain functionality now in resolve_response, and
# we could have a generic.publish
# one of the problems is that these generic functions are dependent
# on request manipulation: something needs to parse the path as
# a stack, then generic.model expects this stack to be there,
# and resolve_response expects a view name to be there.
# this makes the contract between these functions rather tightly
# coupled. Is there a way to loosen the contract?


# XXX find a better place for this kind of API doc. perhaps revise
# the way .all works as a keyword argument to function call?
# a consumer consumes steps in a stack to find an object.
# a consumer function has this signature:
# def consumer(obj, stack, lookup):
#         """Consumes steps.
#         Returns a boolean meaning that some stack has been consumed,
#         an object and the rest of unconsumed stack
#         """

def resolve_model(obj, stack, lookup):
    """Resolve path to a model using consumers.
    """
    # if there is no stack, we consume toward a root model
    if not stack:
        for consumer in generic.consumer.all(obj, lookup=lookup):
            any_consumed, obj, unconsumed = consumer(obj, stack, lookup)
            if any_consumed:
                break
        return obj, stack, lookup
    # consume steps toward model
    unconsumed = stack[:]
    while unconsumed:
        for consumer in generic.consumer.all(obj, lookup=lookup):
            any_consumed, obj, unconsumed = consumer(
                obj, unconsumed, lookup)
            if any_consumed:
                # get new lookup for whatever we found if it exists
                lookup = generic.lookup(obj, lookup=lookup, default=lookup)
                break
        else:
            # nothing could be consumed
            break
    return obj, unconsumed, lookup


def resolve_response(request, model, stack):
    name = get_view_step(model, stack)

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


def publish(request, root):
    #path = self.base_path(request)
    stack = parse_path(request.path)
    model, crumbs, lookup = resolve_model(root, stack, request.lookup)
    request.lookup = lookup
    try:
        return resolve_response(request, model, crumbs)
    except HTTPException as e:
        return e.get_response(request.environ)

# def base_path(self, request):
#     path = request.path
#     script_name = request.script_name
#     if path.startswith(script_name):
#         return path[len(script_name):]
#     return path
