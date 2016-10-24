import morepath
from webob.exc import HTTPNotFound
from webtest import TestApp as Client
import pytest


def test_404_http_exception():
    class app(morepath.App):
        pass

    @app.path(path='')
    class Root(object):
        pass

    c = Client(app())
    c.get('/', status=404)


def test_other_exception_not_handled():
    class app(morepath.App):
        pass

    class MyException(Exception):
        pass

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root)
    def root_default(self, request):
        raise MyException()

    c = Client(app())

    # the WSGI web server will handle any unhandled errors and turn
    # them into 500 errors
    with pytest.raises(MyException):
        c.get('/')


def test_http_exception_excview():
    class app(morepath.App):
        pass

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=HTTPNotFound)
    def notfound_default(self, request):
        return "Not found!"

    c = Client(app())
    response = c.get('/')
    assert response.body == b'Not found!'


def test_other_exception_excview():
    class app(morepath.App):
        pass

    class MyException(Exception):
        pass

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root)
    def root_default(self, request):
        raise MyException()

    @app.view(model=MyException)
    def myexception_default(self, request):
        return "My exception"

    c = Client(app())

    response = c.get('/')
    assert response.body == b'My exception'


def test_http_exception_excview_retain_status():
    class app(morepath.App):
        pass

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=HTTPNotFound)
    def notfound_default(self, request):
        def set_status(response):
            response.status_code = self.code
        request.after(set_status)
        return "Not found!!"

    c = Client(app())
    response = c.get('/', status=404)
    assert response.body == b'Not found!!'


def test_excview_named_view():
    class app(morepath.App):
        pass

    @app.path(path='')
    class Root(object):
        pass

    class MyException(Exception):
        pass

    @app.view(model=Root, name='view')
    def view(self, request):
        raise MyException()

    # the view name should have no infleunce on myexception lookup
    @app.view(model=MyException)
    def myexception_default(self, request):
        return "My exception"

    c = Client(app())
    response = c.get('/view')
    assert response.body == b'My exception'


def test_excview_in_mounted_app():
    class App(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @App.mount(app=Sub, path='sub')
    def mount_sub():
        return Sub()

    class Error(Exception):
        pass

    @Sub.view(model=Error)
    def error_default(self, request):
        return "Default error"

    @Sub.path(path='/')
    class SubRoot(object):
        pass

    @Sub.view(model=SubRoot)
    def subroot_default(self, request):
        raise Error()

    c = Client(App())
    response = c.get('/sub')
    assert response.body == b'Default error'
