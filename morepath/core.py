from .app import global_app
from .config import Config
from .model import Mount
import morepath.directive
from morepath import generic
from .app import AppBase
from .error import LinkError
from .request import Request, Response
from .converter import Converter, IDENTITY_CONVERTER
from werkzeug.wrappers import BaseResponse
from werkzeug.exceptions import Unauthorized
import morepath
from reg import mapply, KeyIndex
from datetime import datetime, date
from time import mktime, strptime


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
    value, stack, traject_variables = traject.consume(request.unconsumed)
    if value is None:
        return None
    get_model, get_parameters = value
    variables = get_parameters(request.args)
    variables.update(generic.context(model, default={}, lookup=lookup))
    variables['parent'] = model
    variables['request'] = request
    variables.update(traject_variables)
    next_model = mapply(get_model, **variables)
    if next_model is None:
        return None
    request.unconsumed = stack
    return next_model


@global_app.function(generic.path, object)
def app_path(model, lookup):
    app = generic.app(model, lookup=lookup, default=None)
    if app is None:
        raise LinkError()
    traject = generic.traject(app, lookup=lookup)
    return traject.path(model)


@global_app.function(generic.link, Request, object, object)
def link(request, model, mounted):
    result = []
    parameters = {}
    while mounted is not None:
        path, params = generic.path(model, lookup=mounted.lookup())
        result.append(path)
        parameters.update(params)
        model = mounted
        mounted = mounted.parent()
    result.reverse()
    return '/'.join(result).strip('/'), parameters


@global_app.function(generic.traject, AppBase)
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


@global_app.converter(type=int)
def int_converter():
    return Converter(int)


@global_app.converter(type=str)
def str_converter():
    # XXX do we want to decode/encode unicode?
    return IDENTITY_CONVERTER


@global_app.converter(type=unicode)
def unicode_converter():
    return IDENTITY_CONVERTER


def date_decode(s):
    return date.fromtimestamp(mktime(strptime(s, '%Y%m%d')))


def date_encode(d):
      return d.strftime('%Y%m%d')


@global_app.converter(type=date)
def date_converter():
    return Converter(date_decode, date_encode)


def datetime_decode(s):
    return datetime.fromtimestamp(mktime(strptime(s, '%Y%m%dT%H%M%S')))


def datetime_encode(d):
    return d.strftime('%Y%m%dT%H%M%S')


@global_app.converter(type=datetime)
def datetime_converter():
    return Converter(datetime_decode, datetime_encode)
