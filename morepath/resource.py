from morepath import generic
from .request import Request
from reg import PredicateRegistry, Predicate, KeyIndex, Matcher
import json


class Resource(object):
    def __init__(self, resource, render):
        self.resource = resource
        self.render = render

    def __call__(self, request, model):
        return self.resource(request, model)


class ResourceMatcher(Matcher):
    def __init__(self):
        self.reg = PredicateRegistry([Predicate('name', KeyIndex),
                                      Predicate('request_method', KeyIndex)])

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
        matcher = registry.exact(generic.resource, (Request, model))
        if matcher is None:
            matcher = ResourceMatcher()
        matcher.register(predicates, registration)
        registration = matcher
    registry.register(generic.resource, (Request, model), registration)


def render_noop(response, content):
    return response


def render_json(response, content):
    response.content_type = 'application/json'
    response.set_data(json.dumps(content))
    return response


def render_html(response, content):
    response.content_type = 'text/html'
    response.set_data(content)
    return response
