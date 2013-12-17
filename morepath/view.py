from morepath import generic
from .request import Request, Response
from reg import PredicateMatcher, Predicate, KeyIndex
import json


class View(object):
    def __init__(self, func, render, permission):
        self.func = func
        self.render = render
        self.permission = permission

    def __call__(self, request, model):
        return self.func(request, model)


# XXX what happens if predicates is None for one registration
# but filled for another?
def register_view(registry, model, view, render=None, permission=None,
                  predicates=None):
    if permission is not None:
        # instantiate permission class so it can be looked up using reg
        permission = permission()
    registration = View(view, render, permission)
    if predicates is not None:
        matcher = registry.exact(generic.view, (Request, model))
        if matcher is None:
            matcher = PredicateMatcher(
                registry.exact('predicate_info', ()))
        matcher.register(predicates, registration)
        registration = matcher
    registry.register(generic.view, (Request, model), registration)


def register_predicate(registry, func, name, index, order):
    predicate_info = registry.exact('predicate_info', ())
    if predicate_info is None:
        predicate_info = []
        registry.register('predicate_info', (), predicate_info)
    predicate_info.append((Predicate(name, index, -order), func))


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
