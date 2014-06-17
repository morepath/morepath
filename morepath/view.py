from morepath import generic
from .request import Request, Response
from reg import PredicateMatcher, Predicate, ANY
import json
from webob.exc import HTTPFound


class View(object):
    def __init__(self, func, render, permission, internal):
        self.func = func
        self.render = render
        self.permission = permission
        self.internal = internal

    def __call__(self, request, model):
        # the argument order is reversed here for the actual view function
        # this still makes request weigh stronger in multiple dispatch,
        # but lets view authors write 'self, request'.
        return self.func(model, request)


# XXX what happens if predicates is None for one registration
# but filled for another?
def register_view(registry, model, view, render=None, permission=None,
                  internal=False, predicates=None):
    if permission is not None:
        # instantiate permission class so it can be looked up using reg
        permission = permission()
    registration = View(view, render, permission, internal)
    if predicates is not None:
        registration = get_predicate_registration(registry, model,
                                                  predicates, registration)
    registry.register(generic.view, (Request, model), registration)


def get_predicate_registration(registry, model, predicates, registration):
    predicate_info = registry.exact('predicate_info', ())
    predicates = get_predicates_with_defaults(predicates, predicate_info)
    matcher = registry.exact(generic.view, (Request, model))
    if matcher is None:
        predicate_infos = list(predicate_info.values())
        predicate_infos.sort()
        matcher = PredicateMatcher(
            [predicate for (order, predicate) in predicate_infos])
    matcher.register(predicates, registration)
    for order, predicate in predicate_info.values():
        fallback = getattr(predicate, 'fallback', None)
        if fallback is None:
            continue
        if predicates[predicate.name] is ANY:
            continue
        p = predicates.copy()
        p[predicate.name] = ANY
        matcher.register(p, View(fallback, None, None, False))
    return matcher


def get_predicates_with_defaults(predicates, predicate_info):
    result = {}
    for order, predicate in predicate_info.values():
        value = predicates.get(predicate.name)
        if value is None:
            value = predicate.default
        result[predicate.name] = value
    return result


def register_predicate(registry, name, order, default, index, calc):
    # reverse parameters to be consistent with view
    def self_request_calc(self, request):
        return calc(request, self)
    predicate_info = registry.exact('predicate_info', ())
    if predicate_info is None:
        predicate_info = {}
        registry.register('predicate_info', (), predicate_info)
    predicate_info[name] = order, Predicate(name, index,
                                            self_request_calc, default)


def register_predicate_fallback(registry, name, obj):
    predicate_info = registry.exact('predicate_info', ())
    # XXX raise configuration error
    info = predicate_info.get(name)
    assert info is not None
    order, predicate = info
    predicate.fallback = obj


def render_json(content):
    """Take dict/list/string/number content and return json response.
    """
    return Response(json.dumps(content), content_type='application/json')


def render_html(content):
    """Take string and return text/html response.
    """
    return Response(content, content_type='text/html')


def redirect(location):
    return HTTPFound(location=location)
