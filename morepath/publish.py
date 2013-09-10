from .interfaces import (IResponse, ILookup,
                         ResourceError, ModelError, IConsumer)
from .pathstack import parse_path, create_path, DEFAULT, RESOURCE
from .request import Response
from werkzeug.exceptions import HTTPException, NotFound

SHORTCUTS = {
    '@@': RESOURCE,
    }

DEFAULT_NAME = u''


class ResponseSentinel(object):
    pass


RESPONSE_SENTINEL = ResponseSentinel()


def resolve_model(obj, stack, lookup):
    """Resolve path to a model using consumers.
    """
    # we need to consume towards a root
    if not stack:
        for consumer in IConsumer.all(obj, lookup=lookup):
            any_consumed, obj, unconsumed = consumer(obj, stack, lookup)
            if any_consumed:
                break
        return obj, stack, lookup
    # consume steps
    unconsumed = stack[:]
    while unconsumed:
        for consumer in IConsumer.all(obj, lookup=lookup):
            any_consumed, obj, unconsumed = consumer(
                obj, unconsumed, lookup)
            if any_consumed:
                # get new lookup for whatever we found if it exists
                lookup = ILookup.adapt(obj, lookup=lookup, default=lookup)
                break
        else:
            # nothing could be consumed
            break
    return obj, unconsumed, lookup

def resolve_response(request, model, stack):
    ns, name = get_resource_step(model, stack)

    if ns not in (DEFAULT, RESOURCE):
        # XXX also report on resource name
        raise ResourceError(
            "namespace %r is not supported:" % ns)

    request.set_resolver_info({'name': name})

    response = IResponse.adapt(request, model, default=RESPONSE_SENTINEL,
                               lookup=request.lookup)
    if response is RESPONSE_SENTINEL:
        # XXX lookup error resource and fallback to default
        raise NotFound()
    return response


def get_resource_step(model, stack):
    unconsumed_amount = len(stack)
    if unconsumed_amount == 0:
        return RESOURCE, DEFAULT_NAME
    elif unconsumed_amount == 1:
        return stack[0]
    raise ModelError(
        "%r has unresolved path %s" % (model, create_path(stack)))

def publish(request, root):
    #path = self.base_path(request)
    stack = parse_path(request.path, SHORTCUTS)
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

# XXX speculative code that implements request.render. This will
# use a IRenderFactory instead of a IResponseFactory to get the result
# in the case of JSON, this will not serialize the JSON; it might
# simply return the original result in most cases
# request needs to be able to access the publisher now; it
# might start to make sense to make the publisher part of the request,
# in which case lookup is too. or should publisher be a global?
# def render(self, request, model, name=''):
#     resource = self.resource_resolver(request, model, [(RESOURCE, name)])
#     factory = IResponseFactory.adapt(resource, lookup=self.lookup)
#     return factory()

        # return resource(request, model)

        # this renderer needs to be resolved into an IResponse
        #factory = IResponseFactory(resource)
        #return factory()
