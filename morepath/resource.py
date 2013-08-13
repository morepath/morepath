from .interfaces import IResource, IResponseFactory
from .request import Request
from comparch import PredicateRegistry
import json

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

# XXX want to reverse the approach so that what is registered is a
# full IResponseFactory or something adaptable to it. This can then also
# contain the renderer. A function is wrapped into such a resource
# before registration.
def register_resource(registry, model, resource, renderer=None, predicates=None):
    # XXX should predicates ever be None?
    if predicates is None:
        predicates = {}
    lookup = registry.exact_get(IResource, (Request, model))
    if lookup is None:
        lookup = PredicateLookup(PredicateRegistry(PREDICATES))
        registry.register(IResource, (Request, model), lookup)
    resource.renderer = renderer
    lookup.predicate_registry.register(predicates, resource)
    
class FunctionResource(IResponseFactory):
    def __init__(self, func, request, model):
        self.func = func
        self.request = request
        self.model = model
        
    def __call__(self):
        # XXX but what if same function is registered as multiple
        # resources? that is not possible using decorator approach though
        renderer = self.func.renderer
        if renderer is None:
            renderer = noop_renderer
        result = self.func(self.request, self.model)
        return renderer(result)
    
def noop_renderer(data):
    return data

# XXX use response object?
def json_renderer(data):
    return json.dumps(data)
    
