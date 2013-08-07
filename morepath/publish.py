from .pathstack import parse_path, RESOURCE
from .resolve import resolve_model, resolve_resource
from .request import Response
from .interfaces import IResponseFactory

SHORTCUTS = {
    '@@': RESOURCE,
    }


def publish(request, root, lookup):
    #path = self.base_path(request)
    stack = parse_path(request.path, SHORTCUTS)
    def get_lookup(lookup, obj):
        return None
    model, crumbs, lookup = resolve_model(root, stack, lookup,
                                          get_lookup)
    # the model itself is capable of producing a response
    if not crumbs:
        if isinstance(model, Response):
            return model
        elif isinstance(model, IResponseFactory):
            return model()
    # find resource (either default or through last step on crumbs)
    resource = resolve_resource(request, model, crumbs, lookup)
    # XXX IResponseFactory should do something involving renderer
    factory = IResponseFactory.adapt(resource, lookup=lookup)
    return factory()

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
    factory = IRenderFactory.adapt(resource, lookup=self.lookup)
    return factory()
    
        # return resource(request, model)

        # this renderer needs to be resolved into an IResponse
        #factory = IResponseFactory(resource)
        #return factory()
