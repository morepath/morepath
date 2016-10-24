"""This module contains default Morepath configuration shared by
all Morepath applications. It is the only part of the Morepath
implementation that uses directives like user of Morepath does.

It uses Morepath directives to configure:

* view predicates (for model, request method, etc), including
  what HTTP errors should be returned when a view cannot be matched.

* converters for common Python values (int, date, etc)

* a tween that catches exceptions raised by application code
  and looks up an exception view for it.

* a default exception view for HTTP exceptions defined by
  :mod:`webob.exc`, i.e. subclasses of :class:`webob.exc.HTTPException`.

Should you wish to do so you could even override these directives in a
subclass of :class:`morepath.App`. We do not guarantee we won't break
your code with future version of Morepath if you do that, though.
"""
import re

from reg import KeyIndex, ClassIndex
from datetime import datetime, date
from time import mktime, strptime

from webob.exc import (
    HTTPException, HTTPNotFound, HTTPMethodNotAllowed,
    HTTPUnprocessableEntity, HTTPOk, HTTPRedirection, HTTPBadRequest)

from .app import App
from .converter import Converter, IDENTITY_CONVERTER


@App.predicate(App.get_view, name='model', default=None, index=ClassIndex)
def model_predicate(self, obj, request):
    """match model argument by class.

    Predicate for :meth:`morepath.App.view`.
    """
    return obj.__class__


@App.predicate_fallback(App.get_view, model_predicate)
def model_not_found(self, obj, request):
    """if model not matched, HTTP 404.

    Fallback for :meth:`morepath.App.view`.
    """
    raise HTTPNotFound()


@App.predicate(App.get_view, name='name', default='', index=KeyIndex,
               after=model_predicate)
def name_predicate(self, obj, request):
    """match name argument with request.view_name.

    Predicate for :meth:`morepath.App.view`.
    """
    return request.view_name


@App.predicate_fallback(App.get_view, name_predicate)
def name_not_found(self, obj, request):
    """if name not matched, HTTP 404.

    Fallback for :meth:`morepath.App.view`.
    """
    raise HTTPNotFound()


@App.predicate(App.get_view, name='request_method', default='GET',
               index=KeyIndex, after=name_predicate)
def request_method_predicate(self, obj, request):
    """match request method.

    Predicate for :meth:`morepath.App.view`.
    """
    return request.method


@App.predicate_fallback(App.get_view, request_method_predicate)
def method_not_allowed(self, obj, request):
    """if request predicate not matched, method not allowed.

    Fallback for :meth:`morepath.App.view`.
    """
    raise HTTPMethodNotAllowed()


@App.predicate(App.get_view, name='body_model', default=object,
               index=ClassIndex, after=request_method_predicate)
def body_model_predicate(self, obj, request):
    """match request.body_obj with body_model by class.

    Predicate for :meth:`morepath.App.view`.
    """
    # optimization: if we have a GET request, a common case,
    # then there is no point in accessing the body.
    if request.method == 'GET':
        return None.__class__
    return request.body_obj.__class__


@App.predicate_fallback(App.get_view, body_model_predicate)
def body_model_unprocessable(self, obj, request):
    """if body_model not matched, 422.

    Fallback for :meth:`morepath.App.view`.
    """
    raise HTTPUnprocessableEntity()


@App.converter(type=int)
def int_converter():
    """Converter for int."""
    return Converter(int)


@App.converter(type=type(u""))
def unicode_converter():
    """Converter for text."""
    return IDENTITY_CONVERTER


# Python 2
if type(u"") != type(""):  # pragma: no cover  # noqa
    @App.converter(type=type(""))
    def str_converter():
        """Converter for non-text str."""
        # XXX do we want to decode/encode unicode?
        return IDENTITY_CONVERTER


def date_decode(s):
    return date.fromtimestamp(mktime(strptime(s, '%Y%m%d')))


def date_encode(d):
    return d.strftime('%Y%m%d')


@App.converter(type=date)
def date_converter():
    """Converter for date."""
    return Converter(date_decode, date_encode)


def datetime_decode(s):
    return datetime.fromtimestamp(mktime(strptime(s, '%Y%m%dT%H%M%S')))


def datetime_encode(d):
    return d.strftime('%Y%m%dT%H%M%S')


@App.converter(type=datetime)
def datetime_converter():
    """Converter for datetime."""
    return Converter(datetime_decode, datetime_encode)


@App.tween_factory()
def excview_tween_factory(app, handler):
    """Exception views.

    If an exception is raised by application code and a view is
    declared for that exception class, use it.

    If no view can be found, raise it all the way up -- this will be a
    500 internal server error and an exception logged.
    """
    def excview_tween(request):
        try:
            response = handler(request)
        except Exception as exc:
            # we must use component_by_keys here because we
            # do not want the request to feature in the lookup;
            # we don't want its request method or name to influence
            # exception lookup
            view = request.app.get_view.component_by_keys(model=exc.__class__)
            if view is None:
                raise

            # we don't want to run any after already set in the exception view
            if not isinstance(exc, (HTTPOk, HTTPRedirection)):
                request.clear_after()

            return view(app, exc, request)
        return response
    return excview_tween


@App.tween_factory(over=excview_tween_factory)
def poisoned_host_header_protection_tween_factory(app, handler):
    """Protect Morepath applications against the most basic host header
    poisoning attacts.

    The regex approach has been copied from the Django project. To find more
    about this particular kind of attack have a look at the following
    references:

    * http://skeletonscribe.net/2013/05/practical-http-host-header-attacks
    * https://www.djangoproject.com/weblog/2012/dec/10/security/
    * https://github.com/django/django/commit/77b06e41516d8136b56c040cba7e235b

    """
    valid_host_re = re.compile(
        r"^([a-z0-9.-]+|\[[a-f0-9]*:[a-f0-9:]+\])(:\d+)?$")

    def poisoned_host_header_protection_tween(request):
        if not valid_host_re.match(request.host):
            return HTTPBadRequest("Invalid HOST header")

        return handler(request)

    return poisoned_host_header_protection_tween


@App.view(model=HTTPException)
def standard_exception_view(self, request):
    """We want the webob standard responses for any webob-based HTTP exception.

    Applies to subclasses of :class:`webob.HTTPException`.
    """
    # webob HTTPException is a response already
    return self
