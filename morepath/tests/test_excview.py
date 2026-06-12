from __future__ import annotations

import pytest
from webob.exc import HTTPNotFound
from webtest import TestApp as Client

import morepath


def test_404_http_exception() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        pass

    c = Client(app())
    c.get("/", status=404)


def test_other_exception_not_handled() -> None:
    class app(morepath.App):
        pass

    class MyException(Exception):
        pass

    @app.path(path="")
    class Root:
        pass

    @app.view(model=Root)
    def root_default(self: Root, request: morepath.Request) -> None:
        raise MyException()

    c = Client(app())

    # the WSGI web server will handle any unhandled errors and turn
    # them into 500 errors
    with pytest.raises(MyException):
        c.get("/")


def test_http_exception_excview() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        pass

    @app.view(model=HTTPNotFound)
    def notfound_default(self: HTTPNotFound, request: morepath.Request) -> str:
        return "Not found!"

    c = Client(app())
    response = c.get("/")
    assert response.body == b"Not found!"


def test_other_exception_excview() -> None:
    class app(morepath.App):
        pass

    class MyException(Exception):
        pass

    @app.path(path="")
    class Root:
        pass

    @app.view(model=Root)
    def root_default(self: Root, request: morepath.Request) -> None:
        raise MyException()

    @app.view(model=MyException)
    def myexception_default(
        self: MyException, request: morepath.Request
    ) -> str:
        return "My exception"

    c = Client(app())

    response = c.get("/")
    assert response.body == b"My exception"


def test_http_exception_excview_retain_status() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        pass

    @app.view(model=HTTPNotFound)
    def notfound_default(self: HTTPNotFound, request: morepath.Request) -> str:
        def set_status(response: morepath.Response) -> None:
            response.status_code = self.code

        request.after(set_status)
        return "Not found!!"

    c = Client(app())
    response = c.get("/", status=404)
    assert response.body == b"Not found!!"


def test_excview_named_view() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        pass

    class MyException(Exception):
        pass

    @app.view(model=Root, name="view")
    def view(self: Root, request: morepath.Request) -> None:
        raise MyException()

    # the view name should have no influence on myexception lookup
    @app.view(model=MyException)
    def myexception_default(
        self: MyException, request: morepath.Request
    ) -> str:
        return "My exception"

    c = Client(app())
    response = c.get("/view")
    assert response.body == b"My exception"


def test_excview_in_mounted_app() -> None:
    class App(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @App.mount(app=Sub, path="sub")
    def mount_sub() -> Sub:
        return Sub()

    class Error(Exception):
        pass

    @Sub.view(model=Error)
    def error_default(self: Error, request: morepath.Request) -> str:
        return "Default error"

    @Sub.path(path="/")
    class SubRoot:
        pass

    @Sub.view(model=SubRoot)
    def subroot_default(self: SubRoot, request: morepath.Request) -> None:
        raise Error()

    c = Client(App())
    response = c.get("/sub")
    assert response.body == b"Default error"
