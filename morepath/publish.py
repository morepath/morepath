from .pathstack import parse_path, RESOURCE
from .resolve import ModelResolver, ResourceResolver

SHORTCUTS = {
    '@@': RESOURCE,
    }

class Publisher(object):
    def __init__(self, lookup):
        self.model_resolver = ModelResolver(lookup)
        self.resource_resolver = ResourceResolver(lookup)
    
    # def base_path(self, request):
    #     path = request.path
    #     script_name = request.script_name
    #     if path.startswith(script_name):
    #         return path[len(script_name):]
    #     return path

    def publish(self, request, root):
        #path = self.base_path(request)
        stack = parse_path(request.path, SHORTCUTS)

        model, crumbs = self.model_resolver(root, stack)
        # the model itself is capable of producing a response
        # if not crumbs:
        #     if isinstance(model, Response):
        #         return model
        #     elif isinstance(model, IResponseFactory):
        #         return model()
        # there is a default resource or an extra path step with the resource
        resource = self.resource_resolver(request, model, crumbs)
        return resource(request, model)

        # this renderer needs to be resolved into an IResponse
        #factory = IResponseFactory(resource)
        #return factory()
