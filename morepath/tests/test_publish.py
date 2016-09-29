import dectate
import morepath
from morepath.app import App
from morepath.publish import publish, resolve_response
from morepath.request import Response
from morepath.view import render_json, render_html
from webob.exc import HTTPNotFound, HTTPBadRequest, HTTPFound, HTTPOk
import webob
from webtest import TestApp as Client
import pytest


def get_environ(path, **kw):
    return webob.Request.blank(path, **kw).environ


class Model(object):
    pass


def test_view():
    class app(App):
        pass

    dectate.commit(app)

    def view(self, request):
        return "View!"

    app.config.view_registry.register_view(dict(model=Model), view)

    model = Model()
    result = resolve_response(model, app().request(get_environ(path='')))
    assert result.body == b'View!'


def test_predicates():
    class app(App):
        pass

    dectate.commit(app)

    def view(self, request):
        return "all"

    def post_view(self, request):
        return "post"

    view_registry = app.config.view_registry

    view_registry.register_view(dict(model=Model), view)
    view_registry.register_view(
        dict(model=Model, request_method='POST'),
        post_view)

    model = Model()
    assert resolve_response(
        model, app().request(get_environ(path=''))).body == b'all'
    assert (
        resolve_response(
            model, app().request(get_environ(path='', method='POST'))).body ==
        b'post')


def test_notfound():
    class app(App):
        pass

    dectate.commit(app)

    request = app().request(get_environ(path=''))

    with pytest.raises(HTTPNotFound):
        publish(request)


def test_notfound_with_predicates():
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self, request):
        return "view"

    app.config.view_registry.register_view(dict(model=Model), view)

    model = Model()
    request = app().request(get_environ(''))
    request.unconsumed = ['foo']
    with pytest.raises(HTTPNotFound):
        resolve_response(model, request)


def test_response_returned():
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self, request):
        return Response('Hello world!')

    app.config.view_registry.register_view(dict(model=Model), view)

    model = Model()
    response = resolve_response(model, app().request(get_environ(path='')))
    assert response.body == b'Hello world!'


def test_request_view():
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self, request):
        return {'hey': 'hey'}

    app.config.view_registry.register_view(
        dict(model=Model), view,
        render=render_json)

    request = app().request(get_environ(path=''))

    model = Model()
    response = resolve_response(model, request)
    # when we get the response, the json will be rendered
    assert response.body == b'{"hey": "hey"}'
    assert response.content_type == 'application/json'
    # but we get the original json out when we access the view
    assert request.view(model) == {'hey': 'hey'}


def test_request_view_with_predicates():
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self, request):
        return {'hey': 'hey'}

    app.config.view_registry.register_view(
        dict(model=Model, name='foo'), view,
        render=render_json)

    request = app().request(get_environ(path=''))

    model = Model()
    # since the name is set to foo, we get nothing here
    assert request.view(model) is None
    # we have to pass the name predicate ourselves
    assert request.view(model, name='foo') == {'hey': 'hey'}
    # the predicate information in the request is ignored when we do a
    # manual view lookup using request.view
    request = app().request(get_environ(path='foo'))
    assert request.view(model) is None


def test_render_html():
    class app(App):
        pass

    dectate.commit(app)

    def view(self, request):
        return '<p>Hello world!</p>'

    app.config.view_registry.register_view(
        dict(model=Model), view,
        render=render_html)

    request = app().request(get_environ(path=''))
    model = Model()
    response = resolve_response(model, request)
    assert response.body == b'<p>Hello world!</p>'
    assert response.content_type == 'text/html'


def test_view_raises_http_error():
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self, request):
        raise HTTPBadRequest()

    path_registry = app.config.path_registry

    path_registry.register_path(
        Model, 'foo', None, None, None, None, False, Model)

    app.config.view_registry.register_view(dict(model=Model), view)

    request = app().request(get_environ(path='foo'))

    with pytest.raises(HTTPBadRequest):
        publish(request)


def test_view_after():
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self, request):
        @request.after
        def set_header(response):
            response.headers.add('Foo', 'FOO')
        return "View!"

    app.config.view_registry.register_view(
        dict(model=Model),
        view)

    model = Model()
    result = resolve_response(model, app().request(get_environ(path='')))
    assert result.body == b'View!'
    assert result.headers.get('Foo') == 'FOO'


def test_view_after_redirect():
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self, request):
        @request.after
        def set_header(response):
            response.headers.add('Foo', 'FOO')
        return morepath.redirect('http://example.org')

    app.config.view_registry.register_view(
        dict(model=Model),
        view)

    model = Model()
    result = resolve_response(model, app().request(get_environ(path='')))
    assert result.status_code == 302
    assert result.headers.get('Location') == 'http://example.org'
    assert result.headers.get('Foo') == 'FOO'


def test_conditional_view_after():
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self, request):
        if False:
            @request.after
            def set_header(response):
                response.headers.add('Foo', 'FOO')
        return "View!"

    app.config.view_registry.register_view(
        dict(model=Model), view)

    model = Model()
    result = resolve_response(model, app().request(get_environ(path='')))
    assert result.body == b'View!'
    assert result.headers.get('Foo') is None


def test_view_after_non_decorator():
    class app(morepath.App):
        pass

    dectate.commit(app)

    def set_header(response):
        response.headers.add('Foo', 'FOO')

    def view(self, request):
        request.after(set_header)
        return "View!"

    app.config.view_registry.register_view(dict(model=Model), view)

    model = Model()
    result = resolve_response(model, app().request(get_environ(path='')))
    assert result.body == b'View!'
    assert result.headers.get('Foo') == 'FOO'


def test_view_after_doesnt_apply_to_raised_404_exception():
    class App(morepath.App):
        pass

    class Root(object):
        pass

    @App.path(model=Root, path='')
    def get_root():
        return Root()

    @App.view(model=Root)
    def view(self, request):
        @request.after
        def set_header(response):
            response.headers.add('Foo', 'FOO')
        raise HTTPNotFound()

    dectate.commit(App)

    c = Client(App())

    response = c.get('/', status=404)
    assert response.headers.get('Foo') is None


def test_view_after_doesnt_apply_to_returned_404_exception():
    class App(morepath.App):
        pass

    class Root(object):
        pass

    @App.path(model=Root, path='')
    def get_root():
        return Root()

    @App.view(model=Root)
    def view(self, request):
        @request.after
        def set_header(response):
            response.headers.add('Foo', 'FOO')
        return HTTPNotFound()

    dectate.commit(App)

    c = Client(App())

    response = c.get('/', status=404)
    assert response.headers.get('Foo') is None


@pytest.mark.parametrize('status_code,exception_class', [
    (200, HTTPOk),
    (302, HTTPFound)
])
def test_view_after_applies_to_some_exceptions(status_code, exception_class):
    class App(morepath.App):
        pass

    class Root(object):
        pass

    @App.path(model=Root, path='')
    def get_root():
        return Root()

    @App.view(model=Root)
    def view(self, request):
        @request.after
        def set_header(response):
            response.headers.add('Foo', 'FOO')
        raise exception_class()

    dectate.commit(App)

    c = Client(App())

    response = c.get('/', status=status_code)
    assert response.headers.get('Foo') == 'FOO'


def test_view_after_doesnt_apply_to_exception_view():
    class App(morepath.App):
        pass

    class Root(object):
        pass

    class MyException(Exception):
        pass

    @App.path(model=Root, path='')
    def get_root():
        return Root()

    @App.view(model=Root)
    def view(self, request):
        @request.after
        def set_header(response):
            response.headers.add('Foo', 'FOO')
        raise MyException()

    @App.view(model=MyException)
    def exc_view(self, request):
        return "My exception"

    dectate.commit(App)

    c = Client(App())

    response = c.get('/')
    assert response.body == b'My exception'
    assert response.headers.get('Foo') is None
