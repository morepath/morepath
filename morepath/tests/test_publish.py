import morepath
from morepath.app import App
from morepath.publish import publish, resolve_response
from morepath.path import register_path
from morepath.request import Response
from morepath.view import register_view, render_json, render_html
from morepath.core import setup
from webob.exc import HTTPNotFound, HTTPBadRequest
import webob

import pytest


def setup_module(module):
    morepath.disable_implicit()


def get_environ(path, **kw):
    return webob.Request.blank(path, **kw).environ


class Model(object):
    pass


def test_view():
    config = setup()
    app = App(testing_config=config)
    config.commit()

    def view(self, request):
        return "View!"

    register_view(app, Model, view, predicates=dict(name=''))

    model = Model()
    result = resolve_response(app.request(get_environ(path='')), model)
    assert result.body == b'View!'


def test_predicates():
    config = setup()
    app = App(testing_config=config)
    config.commit()

    def view(self, request):
        return "all"

    def post_view(self, request):
        return "post"

    register_view(app, Model, view, predicates=dict(name=''))
    register_view(app, Model, post_view,
                  predicates=dict(name='', request_method='POST'))

    model = Model()
    assert resolve_response(
        app.request(get_environ(path='')), model).body == b'all'
    assert (resolve_response(app.request(get_environ(path='', method='POST')),
                             model).body == b'post')


def test_notfound():
    config = setup()
    app = App(testing_config=config)
    config.commit()

    request = app.request(get_environ(path=''))
    request.mounts.append(app.mounted())

    with pytest.raises(HTTPNotFound):
        publish(request)


def test_notfound_with_predicates():
    config = setup()
    app = App(testing_config=config)
    config.commit()

    def view(self, request):
        return "view"

    register_view(app, Model, view, predicates=dict(name=''))
    model = Model()
    request = app.request(get_environ(''))
    request.unconsumed = ['foo']
    with pytest.raises(HTTPNotFound):
        resolve_response(request, model)


def test_response_returned():
    config = setup()
    app = App(testing_config=config)
    config.commit()

    def view(self, request):
        return Response('Hello world!')

    register_view(app, Model, view)
    model = Model()
    response = resolve_response(app.request(get_environ(path='')), model)
    assert response.body == b'Hello world!'


def test_request_view():
    config = setup()
    app = App(testing_config=config)
    config.commit()

    def view(self, request):
        return {'hey': 'hey'}

    register_view(app, Model, view, render=render_json)

    request = app.request(get_environ(path=''))
    request.mounts = [app]  # XXX should do this centrally

    model = Model()
    response = resolve_response(request, model)
    # when we get the response, the json will be rendered
    assert response.body == b'{"hey": "hey"}'
    assert response.content_type == 'application/json'
    # but we get the original json out when we access the view
    assert request.view(model) == {'hey': 'hey'}


def test_request_view_with_predicates():
    config = setup()
    app = App(testing_config=config)
    config.commit()

    def view(self, request):
        return {'hey': 'hey'}

    register_view(app, Model, view, render=render_json,
                  predicates=dict(name='foo'))

    request = app.request(get_environ(path=''))
    request.mounts = [app]  # XXX should do this centrally

    model = Model()
    # since the name is set to foo, we get nothing here
    assert request.view(model) is None
    # we have to pass the name predicate ourselves
    assert request.view(model, name='foo') == {'hey': 'hey'}
    # the predicate information in the request is ignored when we do a
    # manual view lookup using request.view
    request = app.request(get_environ(path='foo'))
    request.mounts = [app]  # XXX should do this centrally
    assert request.view(model) is None


def test_render_html():
    config = setup()
    app = App(testing_config=config)
    config.commit()

    def view(self, request):
        return '<p>Hello world!</p>'

    register_view(app, Model, view, render=render_html)

    request = app.request(get_environ(path=''))
    model = Model()
    response = resolve_response(request, model)
    assert response.body == b'<p>Hello world!</p>'
    assert response.content_type == 'text/html'


def test_view_raises_http_error():
    config = setup()
    app = App(testing_config=config)
    config.commit()

    def view(self, request):
        raise HTTPBadRequest()

    register_path(app, Model, 'foo', None, None, None, None, Model)
    register_view(app, Model, view)

    request = app.request(get_environ(path='foo'))
    request.mounts.append(app.mounted())

    with pytest.raises(HTTPBadRequest):
        publish(request)


def test_view_after():
    config = setup()
    app = App(testing_config=config)
    config.commit()

    def view(self, request):
        @request.after
        def set_header(response):
            response.headers.add('Foo', 'FOO')
        return "View!"

    register_view(app, Model, view, predicates=dict(name=''))

    model = Model()
    result = resolve_response(app.request(get_environ(path='')), model)
    assert result.body == b'View!'
    assert result.headers.get('Foo') == 'FOO'


def test_conditional_view_after():
    config = setup()
    app = App(testing_config=config)
    config.commit()

    def view(self, request):
        if False:
            @request.after
            def set_header(response):
                response.headers.add('Foo', 'FOO')
        return "View!"

    register_view(app, Model, view, predicates=dict(name=''))

    model = Model()
    result = resolve_response(app.request(get_environ(path='')), model)
    assert result.body == b'View!'
    assert result.headers.get('Foo') is None


def test_view_after_non_decorator():
    config = setup()
    app = App(testing_config=config)
    config.commit()

    def set_header(response):
        response.headers.add('Foo', 'FOO')

    def view(self, request):
        request.after(set_header)
        return "View!"

    register_view(app, Model, view, predicates=dict(name=''))

    model = Model()
    result = resolve_response(app.request(get_environ(path='')), model)
    assert result.body == b'View!'
    assert result.headers.get('Foo') == 'FOO'
