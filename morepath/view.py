from morepath import generic
from .request import Request, Response
from reg import PredicateRegistry, Predicate, KeyIndex, Matcher
import json


class View(object):
    def __init__(self, func, render):
        self.func = func
        self.render = render

    def __call__(self, request, model):
        return self.func(request, model)


class ViewMatcher(Matcher):
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


# XXX what happens if predicates is None for one registration
# but filled for another?
def register_view(registry, model, view, render=None, predicates=None):
    registration = View(view, render)
    if predicates is not None:
        matcher = registry.exact(generic.view, (Request, model))
        if matcher is None:
            matcher = ViewMatcher()
        matcher.register(predicates, registration)
        registration = matcher
    registry.register(generic.view, (Request, model), registration)


def render_noop(response, content):
    return response


def render_json(content):
    response = Response(json.dumps(content))
    response.content_type = 'application/json'
    return response


def render_html(content):
    response = Response(content)
    response.content_type = 'text/html'
    return response
