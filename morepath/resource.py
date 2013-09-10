from .interfaces import IResource
from .request import Request
from comparch import PredicateRegistry, KeyPredicate
from comparch.interfaces import IMatcher
import json


class PredicateLookup(IResource):
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


class Resource(IResource):
    def __init__(self, resource, render):
        self.resource = resource
        self.render = render

    def __call__(self, request, model):
        return self.resource(request, model)


class ResourceMatcher(IMatcher):
    def __init__(self):
        self.reg = PredicateRegistry([KeyPredicate('name'),
                                      KeyPredicate('request_method')])

    def register(self, predicates, registration):
        self.reg.register(predicates, registration)

    def get_predicates(self, request):
        result = {}
        result['request_method'] = request.method
        result['name'] = request.resolver_info()['name']
        return result

    def __call__(self, request, model):
        request_predicates = self.get_predicates(request)
        return self.reg.get(request_predicates)


def register_resource(registry, model, resource, render=None, predicates=None):
    registration = Resource(resource, render)
    if predicates is not None:
        matcher = registry.exact_get(IResource, (Request, model))
        if matcher is None:
            matcher = ResourceMatcher()
        matcher.register(predicates, registration)
        registration = matcher
    registry.register(IResource, (Request, model), registration)


def render_noop(response, content):
    return response


def render_json(response, content):
    response.set_data(json.dumps(content))
    return response
