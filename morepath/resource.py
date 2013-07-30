from comparch import PredicateRegistry

from .interfaces import IResource, IResponseFactory, ResourceError
from .request import Request

# XXX hardcoded predicates gotta change
PREDICATES = ['name', 'request_method']

class PredicateLookup(object):
    def __init__(self, predicate_registry):
        self.predicate_registry = predicate_registry

    def __call__(self, request, model):
        component = self.predicate_registry.get(self.get_predicates(request))
        # XXX but wait; it could be that a matching set of predicates is
        # registered for a base class, and now that never would be found!
        # if some predicates match for elephant and a non-overlapping set of
        # predicates are registered for animal, and the match is not for
        # elephant, it should really find the match for animal if that's
        # there, but right now it won't
        if component is None:
            return None
        # XXX check for function type?
        return FunctionResource(component, request, model)
    
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
    
class FunctionResource(IResponseFactory):
    def __init__(self, func, request, model):
        self.func = func
        self.request = request
        self.model = model

    def __call__(self):
        return self.func(self.request, self.model)
