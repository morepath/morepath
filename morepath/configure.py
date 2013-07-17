from comparch import PredicateRegistry

from .interfaces import IResource, ResourceError
from .request import Request

# XXX hardcoded predicates gotta change
PREDICATES = ['name', 'request_method']

class PredicateLookup(object):
    def __init__(self, predicate_registry):
        self.predicate_registry = predicate_registry

    def __call__(self, request, model):
        func = self.predicate_registry.get(self.get_predicates(request))
        if func is None:
            return None
        return func(request, model)
    
    # XXX move to request?
    def get_predicates(self, request):
        result = {}
        result['request_method'] = request.method
        result['name'] = request.resolver_info()['name']
        return result
    
def register_resource(registry, model, resource, **predicates):
    lookup = registry.exact_get(IResource, (Request, model))
    if lookup is None:
        lookup = PredicateLookup(PredicateRegistry(PREDICATES))
        registry.register(IResource, (Request, model), lookup)
    lookup.predicate_registry.register(predicates, resource)

