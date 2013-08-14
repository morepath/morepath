from .interfaces import IResponse, IApp, ResourceError, ModelError
from .pathstack import parse_path, DEFAULT, RESOURCE
from .request import Response
from .resolve import resolve_model, resolve_resource
from comparch import Lookup

SHORTCUTS = {
    '@@': RESOURCE,
    }

DEFAULT_NAME = u''

class ResponseSentinel(object):
    pass

RESPONSE_SENTINEL = ResponseSentinel()

def get_resource_step(model, stack):
    unconsumed_amount = len(stack)
    if unconsumed_amount == 0:
        return RESOURCE, DEFAULT_NAME
    elif unconsumed_amount == 1:
        return stack[0]
    raise ModelError(
        "%r has unresolved path %s" % (model, create_path(stack)))

def resolve_response(request, model, stack, lookup):
    ns, name = get_resource_step(model, stack)

    if ns not in (DEFAULT, RESOURCE):
        # XXX also report on resource name
        raise ResourceError(
            "namespace %r is not supported:" % ns)

    request.set_resolver_info({'name': name})

    response = IResponse.adapt(request, model, default=RESPONSE_SENTINEL,
                               lookup=lookup)
    if response is RESPONSE_SENTINEL:
        # XXX lookup error resource and fallback to default
        return Response("Not found", 404)
    return response
    
def publish(request, root, lookup):
    #path = self.base_path(request)
    stack = parse_path(request.path, SHORTCUTS)
    model, crumbs, lookup = resolve_model(root, stack, lookup)
    request.lookup = lookup
    response = resolve_response(request, model, crumbs, lookup)
    if isinstance(response, basestring):
        return Response(response)
    return response

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
def render(self, request, model, name=''):
    resource = self.resource_resolver(request, model, [(RESOURCE, name)])
    factory = IResponseFactory.adapt(resource, lookup=self.lookup)
    return factory()
    
        # return resource(request, model)

        # this renderer needs to be resolved into an IResponse
        #factory = IResponseFactory(resource)
        #return factory()
