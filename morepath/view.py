from morepath import generic
from .request import Request, Response
from reg import PredicateMatcher, Predicate
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
        registration = get_predicate_registration(registry, model,
                                                  predicates, registration)
    registry.register(generic.view, (Request, model), registration)


def get_predicate_registration(registry, model, predicates, registration):
    predicate_info = registry.exact('predicate_info', ())
    predicates = get_predicates_with_defaults(predicates, predicate_info)
    matcher = registry.exact(generic.view, (Request, model))
    if matcher is None:
        predicate_info.sort()
        matcher = PredicateMatcher(
            [predicate for (order, predicate) in predicate_info])
    matcher.register(predicates, registration)
    return matcher


def get_predicates_with_defaults(predicates, predicate_info):
    result = {}
    for order, predicate in predicate_info:
        value = predicates.get(predicate.name)
        if value is None:
            value = predicate.default
        result[predicate.name] = value
    return result


def register_predicate(registry, name, order, default, index, calc):
    predicate_info = registry.exact('predicate_info', ())
    if predicate_info is None:
        predicate_info = []
        registry.register('predicate_info', (), predicate_info)
    predicate_info.append((order, Predicate(name, index, calc, default)))


def render_json(content):
    """Take dict/list/string/number content and return application/json response.
    """
    response = Response(json.dumps(content))
    response.content_type = 'application/json'
    return response


def render_html(content):
    """Take string and return text/html response.
    """
    response = Response(content)
    response.content_type = 'text/html'
    return response
