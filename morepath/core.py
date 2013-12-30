from .app import global_app
from .config import Config
from .model import Mount
import morepath.directive
from morepath import generic
from .app import App
from .request import Request, Response
from werkzeug.wrappers import BaseResponse
from werkzeug.exceptions import Unauthorized
import morepath
from reg import mapply, KeyIndex


assert morepath.directive  # we need to make the function directive work


def setup():
    """Set up core Morepath framework configuration.

    Returns a :class:`Config` object; you can then :meth:`Config.scan`
    the configuration of other packages you want to load and then
    :meth:`Config.commit` it.

    See also :func:`autoconfig` and :func:`autosetup`.

    :returns: :class:`Config` object.
    """
    config = Config()
    config.scan(morepath, ignore=['.tests'])
    return config


@global_app.function(generic.consume, Request, object)
def traject_consume(request, model, lookup):
    traject = generic.traject(model, lookup=lookup, default=None)
    if traject is None:
        return None
    get_model, stack, traject_variables = traject(request.unconsumed)
    if get_model is None:
        return None
    variables = generic.context(model, default={}, lookup=lookup)
    variables['base'] = model
    variables['request'] = request
    variables.update(traject_variables)
    next_model = mapply(get_model, **variables)
    if next_model is None:
        return None
    request.unconsumed = stack
    return next_model


@global_app.function(generic.path, object)
def app_path(model, lookup):
    result = []
    while True:
        base = generic.base(model, lookup=lookup, default=None)
        if base is None:
            break
        traject = generic.traject(base, lookup=lookup)
        result.append(traject.path(model))
        model = base
    result.reverse()
    return '/'.join(result)


@global_app.function(generic.link, Request, object, object)
def link(request, model, mounted):
    result = []
    while mounted is not None:
        result.append(app_path(model, lookup=mounted.lookup()))
        model = mounted
        mounted = mounted.parent()
    result.reverse()
    return '/'.join(result).strip('/')


@global_app.function(generic.traject, App)
def app_traject(app):
    return app.traject


@global_app.function(generic.lookup, Mount)
def mount_lookup(model):
    return model.app.lookup()


@global_app.function(generic.traject, Mount)
def mount_traject(model):
    return model.app.traject


@global_app.function(generic.context, Mount)
def mount_context(mount):
    return mount.create_context()


@global_app.function(generic.response, Request, object)
def get_response(request, model):
    view = generic.view.component(
        request, model, lookup=request.lookup,
        default=None)
    if view is None:
        return None
    if not generic.permits(request.identity, model, view.permission,
                           lookup=request.lookup):
        # XXX needs to become forbidden?
        raise Unauthorized()
    content = view(request, model)
    if isinstance(content, BaseResponse):
        # the view took full control over the response
        return content
    # XXX consider always setting a default render so that view.render
    # can never be None
    if view.render is not None:
        response = view.render(content)
    else:
        response = Response(content)
    return response


@global_app.function(generic.permits, object, object, object)
def has_permission(identity, model, permission):
    if permission is None:
        return True
    return False


@global_app.predicate(name='name', index=KeyIndex, order=0,
                      default='')
def name_predicate(request, model):
    return request.view_name


@global_app.predicate(name='request_method', index=KeyIndex, order=1,
                      default='GET')
def request_method_predicate(request, model):
    return request.method
