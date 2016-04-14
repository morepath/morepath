"""
This module contains default Morepath configuration shared by
all Morepath applications.

It uses Morepath directives to configure:

* view predicates (for model, request method, etc), including
  what HTTP errors should be returned when a view cannot be matched.

* converters for common Python values (int, date, etc)

* a tween that catches exceptions raised by application code
  and looks up an exception view for it.

* a default exception view for HTTP exceptions defined by
  :mod:`webob.exc`, i.e. subclasses of :class:`webob.exc.HTTPException`.

"""

import dectate
import importscan

from reg import KeyIndex, ClassIndex
from datetime import datetime, date
from time import mktime, strptime

from webob import Response as BaseResponse, BaseRequest
from webob.exc import (
    HTTPException, HTTPNotFound, HTTPMethodNotAllowed,
    HTTPUnprocessableEntity, HTTPOk, HTTPRedirection)

from . import directive  # install directives with App
from . import generic
from .app import App
from .view import View
from .request import Request, Response
from .converter import Converter, IDENTITY_CONVERTER


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
            # we must use component_key_dict here because we
            # do not want the request to feature in the lookup;
            # we don't want its request method or name to influence
            # exception lookup
            view = generic.view.component_key_dict(model=exc.__class__,
                                                   lookup=request.lookup)
            if view is None:
                raise

            # we don't want to run any after already set in the exception view
            if not isinstance(exc, (HTTPOk, HTTPRedirection)):
                request.clear_after()

            return view(exc, request)
        return response
    return excview_tween


@App.view(model=HTTPException)
def standard_exception_view(self, model):
    # webob HTTPException is a response already
    return self
