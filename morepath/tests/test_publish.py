from morepath.app import App
from morepath.publish import publish, resolve_response
from morepath.model import register_model
from morepath.request import Response
from morepath.view import register_view, render_json, render_html
from morepath.core import setup
from werkzeug.test import EnvironBuilder
from werkzeug.exceptions import NotFound
import pytest


def get_environ(*args, **kw):
    return EnvironBuilder(*args, **kw).get_environ()


class Model(object):
    pass


def test_view():
    app = App()

    c = setup()
    c.configurable(app)
    c.commit()

    def view(request, model):
        return "View!"

    register_view(app, Model, view, predicates=dict(name=''))

    model = Model()
    result = resolve_response(app.request(get_environ(path='')), model)
    assert result.data == 'View!'


def test_predicates():
    app = App()

    c = setup()
    c.configurable(app)
    c.commit()

    def view(request, model):
        return "all"

    def post_view(request, model):
        return "post"

    register_view(app, Model, view, predicates=dict(name=''))
    register_view(app, Model, post_view,
                  predicates=dict(name='', request_method='POST'))

    model = Model()
    assert resolve_response(
        app.request(get_environ(path='')), model).data == 'all'
    assert (resolve_response(app.request(get_environ(path='', method='POST')),
                             model).data == 'post')


def test_notfound():
    app = App()

    c = setup()
    c.configurable(app)
    c.commit()

    response = publish(app.request(get_environ(path='')), app.mounted())
    assert response.status == '404 NOT FOUND'


def test_notfound_with_predicates():
    app = App()

    c = setup()
    c.configurable(app)
    c.commit()

    def view(request, model):
        return "view"

    register_view(app, Model, view, predicates=dict(name=''))
    model = Model()
    request = app.request(get_environ())
    request.unconsumed = ['foo']
    with pytest.raises(NotFound):
        resolve_response(request, model)
    #assert response.status == '404 NOT FOUND'


def test_response_returned():
    app = App()

    c = setup()
    c.configurable(app)
    c.commit()

    def view(request, model):
        return Response('Hello world!')

    register_view(app, Model, view)
    model = Model()
    response = resolve_response(app.request(get_environ(path='')), model)
    assert response.data == 'Hello world!'


def test_request_view():
    app = App()

    c = setup()
    c.configurable(app)
    c.commit()

    def view(request, model):
        return {'hey': 'hey'}

    register_view(app, Model, view, render=render_json)

    request = app.request(get_environ(path=''))
    request.mounts = [app]  # XXX should do this centrally

    model = Model()
    response = resolve_response(request, model)
    # when we get the response, the json will be rendered
    assert response.data == '{"hey": "hey"}'
    assert response.content_type == 'application/json'
    # but we get the original json out when we access the view
    assert request.view(model) == {'hey': 'hey'}


def test_request_view_with_predicates():
    app = App()

    c = setup()
    c.configurable(app)
    c.commit()

    def view(request, model):
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
    app = App()

    c = setup()
    c.configurable(app)
    c.commit()

    def view(request, model):
        return '<p>Hello world!</p>'

    register_view(app, Model, view, render=render_html)

    request = app.request(get_environ(path=''))
    model = Model()
    response = resolve_response(request, model)
    assert response.data == '<p>Hello world!</p>'
    assert response.content_type == 'text/html'


def test_view_raises_http_error():
    app = App()

    c = setup()
    c.configurable(app)
    c.commit()

    from werkzeug.exceptions import BadRequest
    def view(request, model):
        raise BadRequest()

    register_model(app, Model, 'foo', None, None, Model)
    register_view(app, Model, view)

    response = publish(app.request(get_environ(path='foo')), app.mounted())

    assert response.status == '400 BAD REQUEST'


def test_notfound():
    app = App()

    c = setup()
    c.configurable(app)
    c.commit()

    response = publish(app.request(get_environ(path='')), app.mounted())
    assert response.status == '404 NOT FOUND'


def test_view_after():
    app = App()

    c = setup()
    c.configurable(app)
    c.commit()

    def view(request, model):
        @request.after
        def set_header(response):
            response.headers.add('Foo', 'FOO')
        return "View!"

    register_view(app, Model, view, predicates=dict(name=''))

    model = Model()
    result = resolve_response(app.request(get_environ(path='')), model)
    assert result.data == 'View!'
    assert result.headers.get('Foo') == 'FOO'


def test_conditional_view_after():
    app = App()

    c = setup()
    c.configurable(app)
    c.commit()

    def view(request, model):
        if False:
            @request.after
            def set_header(response):
                response.headers.add('Foo', 'FOO')
        return "View!"

    register_view(app, Model, view, predicates=dict(name=''))

    model = Model()
    result = resolve_response(app.request(get_environ(path='')), model)
    assert result.data == 'View!'
    assert result.headers.get('Foo') is None


def test_view_after_non_decorator():
    app = App()

    c = setup()
    c.configurable(app)
    c.commit()

    def set_header(response):
        response.headers.add('Foo', 'FOO')

    def view(request, model):
        request.after(set_header)
        return "View!"

    register_view(app, Model, view, predicates=dict(name=''))

    model = Model()
    result = resolve_response(app.request(get_environ(path='')), model)
    assert result.data == 'View!'
    assert result.headers.get('Foo') == 'FOO'
