from .interfaces import IResponseFactory, IApp
from .pathstack import parse_path, RESOURCE
from .request import Response
from .resolve import resolve_model, resolve_resource
from comparch import Lookup

SHORTCUTS = {
    '@@': RESOURCE,
    }

def publish(request, root, lookup):
    #path = self.base_path(request)
    stack = parse_path(request.path, SHORTCUTS)
    model, crumbs, lookup = resolve_model(root, stack, lookup)
    # the model itself is capable of producing a response
    if not crumbs:
        if isinstance(model, Response):
            return model
        elif isinstance(model, IResponseFactory):
            return model()
    request.lookup = lookup
    # find resource (either default or through last step on crumbs)
    resource = resolve_resource(request, model, crumbs, lookup)
    # XXX IResponseFactory should do something involving renderer
    # XXX special case for a response returning text
    factory = IResponseFactory.adapt(resource, lookup=lookup)
    result = factory()
    if isinstance(result, Response):
        return result
    # XXX handle this at the IResponseFactory adapter level?
    if isinstance(result, basestring):
        return Response(result)
    assert False

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
