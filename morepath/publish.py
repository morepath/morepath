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
        return self.resource_resolver(request, model, crumbs)
    
        # if not crumbs:
        #     if IResponse.providedBy(model):
        #         # The found object can be returned safely.
        #         return model
        #     elif IResponseFactory.providedBy(model):
        #         return model()

        # # The model needs an renderer
        # component = self.view_lookup(request, model, crumbs)
        # if component is None:
        #     raise PublicationError('%r can not be rendered.' % model)

        # # This renderer needs to be resolved into an IResponse
        # factory = IResponseFactory(component)
        # return factory()
