from .config import Config
import morepath.directive
from morepath import generic
from .app import App
from .view import View
from .request import Request, Response
from .converter import Converter, IDENTITY_CONVERTER
from webob import Response as BaseResponse
from webob.exc import (
    HTTPException, HTTPNotFound, HTTPMethodNotAllowed,
    HTTPUnprocessableEntity)
import morepath
from reg import mapply, KeyIndex, ClassIndex
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



@App.function(generic.consume, obj=object)
def traject_consume(request, app, lookup):
    traject = app.traject
    if traject is None:
        return None
    value, stack, traject_variables = traject.consume(request.unconsumed)
    if value is None:
        return None
    get_obj, get_parameters = value
    variables = get_parameters(request.GET)
    variables['request'] = request
    variables['app'] = app
    variables.update(traject_variables)
    next_obj = mapply(get_obj, **variables)
    if next_obj is None:
        return None
    request.unconsumed = stack
    return next_obj


@App.function(generic.link, obj=object)
def link(request, model, mounted):
    result = []
    parameters = {}
    while mounted is not None:
        path_info = generic.path(model, lookup=mounted.lookup)
        if path_info is None:
            return None
        path, params = path_info
        result.append(path)
        parameters.update(params)
        model = mounted
        mounted = mounted.parent
    result.append(request.script_name)
    result.reverse()
    return '/'.join(result).strip('/'), parameters


@App.function(generic.response, obj=object)
def get_response(request, obj):
    view = generic.view.component(request, obj, lookup=request.lookup)
    if view is None:
        # try to look up fallback and use it
        import pdb; pdb.set_trace()
        fallback = generic.view.fallback(request, obj, lookup=request.lookup)
        if fallback is None:
            return None
        return fallback(request, obj)
    return view.response(request, obj)


@App.function(generic.permits, obj=object, identity=object,
              permission=object)
def has_permission(identity, model, permission):
    return False


@App.predicate(generic.view, name='model', default=None, index=ClassIndex)
def model_predicate(obj):
    return obj.__class__


@App.predicate_fallback(generic.view, model_predicate)
def model_not_found(self, request):
    raise HTTPNotFound()


@App.predicate(generic.view, name='name', default='', index=KeyIndex,
               after=model_predicate)
def name_predicate(request):
    return request.view_name


@App.predicate_fallback(generic.view, name_predicate)
def name_not_found(self, request):
    raise HTTPNotFound()


@App.predicate(generic.view, name='request_method', default='GET',
               index=KeyIndex, after=name_predicate)
def request_method_predicate(request):
    return request.method


@App.predicate_fallback(generic.view, request_method_predicate)
def method_not_allowed(self, request):
    raise HTTPMethodNotAllowed()


@App.predicate(generic.view, name='body_model', default=object,
               index=ClassIndex, after=request_method_predicate)
def body_model_predicate(request):
    return request.body_obj.__class__


@App.predicate_fallback(generic.view, body_model_predicate)
def body_model_unprocessable(self, request):
    raise HTTPUnprocessableEntity()


@App.converter(type=int)
def int_converter():
    return Converter(int)


@App.converter(type=type(u""))
def unicode_converter():
    return IDENTITY_CONVERTER


# Python 2
if type(u"") != type(""): # flake8: noqa
    @App.converter(type=type(""))
    def str_converter():
        # XXX do we want to decode/encode unicode?
        return IDENTITY_CONVERTER


def date_decode(s):
    return date.fromtimestamp(mktime(strptime(s, '%Y%m%d')))


def date_encode(d):
    return d.strftime('%Y%m%d')


@App.converter(type=date)
def date_converter():
    return Converter(date_decode, date_encode)


def datetime_decode(s):
    return datetime.fromtimestamp(mktime(strptime(s, '%Y%m%dT%H%M%S')))


def datetime_encode(d):
    return d.strftime('%Y%m%dT%H%M%S')


@App.converter(type=datetime)
def datetime_converter():
    return Converter(datetime_decode, datetime_encode)


@App.tween_factory()
def excview_tween_factory(app, handler):
    def excview_tween(request):
        try:
            response = handler(request)
        except Exception as exc:
            view = generic.view.component_key_dict(model=exc.__class__,
                                                   lookup=request.lookup)
            if view is None:
                raise
            response = view.response(request, exc)
            if response is None:
                raise
            return response
        return response
    return excview_tween


@App.view(model=HTTPException)
def standard_exception_view(self, model):
    # webob HTTPException is a response already
    return self
