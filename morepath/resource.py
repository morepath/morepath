from .interfaces import IResourceRegistration
from .request import Request
from comparch import PredicateRegistry
import json

# XXX hardcoded predicates gotta change
PREDICATES = ['name', 'request_method']


class PredicateLookup(IResourceRegistration):
    def __init__(self, predicate_registry):
        self.predicate_registry = predicate_registry

    def __call__(self, request, model):
        return self.predicate_registry.get(self.get_predicates(request))

        # XXX but wait; it could be that a matching set of predicates is
        # registered for a base class, and now that never would be found!
        # if some predicates match for elephant and a non-overlapping set of
        # predicates are registered for animal, and the match is not for
        # elephant, it should really find the match for animal if that's
        # there, but right now it won't

    # XXX move to request?
    def get_predicates(self, request):
        result = {}
        result['request_method'] = request.method
        result['name'] = request.resolver_info()['name']
        return result


class ResourceRegistration(IResourceRegistration):
    def __init__(self, resource, render):
        self.resource = resource
        self.render = render


def register_resource(registry, model, resource, render=None, predicates=None):
    # XXX should predicates ever be None?
    if predicates is None:
        predicates = {}
    lookup = registry.exact_get(IResourceRegistration, (Request, model))
    if lookup is None:
        lookup = PredicateLookup(PredicateRegistry(PREDICATES))
        registry.register(IResourceRegistration, (Request, model), lookup)
    registration = ResourceRegistration(resource, render)
    lookup.predicate_registry.register(predicates, registration)


def render_noop(content):
    return content


# XXX use response object?
def render_json(content):
    return json.dumps(content)


# we look up IResponseFactory for request and model
