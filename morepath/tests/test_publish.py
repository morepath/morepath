from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
import webob
from webob.exc import HTTPBadRequest, HTTPFound, HTTPNotFound, HTTPOk
from webtest import TestApp as Client

import dectate
import morepath
from morepath.app import App
from morepath.publish import publish, resolve_response
from morepath.request import Response
from morepath.view import View, render_html, render_json

if TYPE_CHECKING:
    from webob import Response as BaseResponse

    from morepath.types import WSGIEnvironment


def get_environ(path: str, **kw: Any) -> WSGIEnvironment:
    return webob.Request.blank(path, **kw).environ


class Model:
    pass


def test_view() -> None:
    class app(App):
        pass

    dectate.commit(app)

    def view(self: object, request: morepath.Request) -> str:
        return "View!"

    app.get_view.register(View(view), model=Model)

    model = Model()
    result = resolve_response(model, app().request(get_environ(path="")))
    assert result.body == b"View!"


def test_predicates() -> None:
    class app(App):
        pass

    dectate.commit(app)

    def view(self: object, request: morepath.Request) -> str:
        return "all"

    def post_view(self: object, request: morepath.Request) -> str:
        return "post"

    app.get_view.register(View(view), model=Model)
    app.get_view.register(View(post_view), model=Model, request_method="POST")

    model = Model()
    assert (
        resolve_response(model, app().request(get_environ(path=""))).body
        == b"all"
    )
    assert (
        resolve_response(
            model, app().request(get_environ(path="", method="POST"))
        ).body
        == b"post"
    )


def test_notfound() -> None:
    class app(App):
        pass

    dectate.commit(app)

    request = app().request(get_environ(path=""))

    with pytest.raises(HTTPNotFound):
        publish(request)


def test_notfound_with_predicates() -> None:
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self: object, request: morepath.Request) -> str:
        return "view"

    app.get_view.register(View(view), model=Model)

    model = Model()
    request = app().request(get_environ(""))
    request.unconsumed = ["foo"]
    with pytest.raises(HTTPNotFound):
        resolve_response(model, request)


def test_response_returned() -> None:
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self: object, request: morepath.Request) -> Response:
        return Response("Hello world!")

    app.get_view.register(View(view), model=Model)

    model = Model()
    response = resolve_response(model, app().request(get_environ(path="")))
    assert response.body == b"Hello world!"


def test_request_view() -> None:
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self: object, request: morepath.Request) -> dict[str, str]:
        return {"hey": "hey"}

    app.get_view.register(View(view, render=render_json), model=Model)

    request = app().request(get_environ(path=""))

    model = Model()
    response = resolve_response(model, request)
    # when we get the response, the json will be rendered
    assert response.body == b'{"hey":"hey"}'
    assert response.content_type == "application/json"
    # but we get the original json out when we access the view
    assert request.view(model) == {"hey": "hey"}


def test_request_view_with_predicates() -> None:
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self: object, request: morepath.Request) -> dict[str, str]:
        return {"hey": "hey"}

    app.get_view.register(
        View(view, render=render_json), model=Model, name="foo"
    )

    request = app().request(get_environ(path=""))

    model = Model()
    # since the name is set to foo, we get nothing here
    assert request.view(model) is None
    # we have to pass the name predicate ourselves
    assert request.view(model, name="foo") == {"hey": "hey"}
    # the predicate information in the request is ignored when we do a
    # manual view lookup using request.view
    request = app().request(get_environ(path="foo"))
    assert request.view(model) is None


def test_render_html() -> None:
    class app(App):
        pass

    dectate.commit(app)

    def view(self: object, request: morepath.Request) -> str:
        return "<p>Hello world!</p>"

    app.get_view.register(View(view, render=render_html), model=Model)

    request = app().request(get_environ(path=""))
    model = Model()
    response = resolve_response(model, request)
    assert response.body == b"<p>Hello world!</p>"
    assert response.content_type == "text/html"


def test_view_raises_http_error() -> None:
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self: object, request: morepath.Request) -> None:
        raise HTTPBadRequest()

    path_registry = app.config.path_registry

    path_registry.register_path(
        Model, "foo", None, None, None, None, False, None, Model
    )

    app.get_view.register(View(view), model=Model)

    request = app().request(get_environ(path="foo"))

    with pytest.raises(HTTPBadRequest):
        publish(request)


def test_view_after() -> None:
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self: object, request: morepath.Request) -> str:
        @request.after
        def set_header(response: Response) -> None:
            response.headers.add("Foo", "FOO")

        return "View!"

    app.get_view.register(View(view), model=Model)

    model = Model()
    result = resolve_response(model, app().request(get_environ(path="")))
    assert result.body == b"View!"
    assert result.headers.get("Foo") == "FOO"


def test_view_after_redirect() -> None:
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self: object, request: morepath.Request) -> BaseResponse:
        @request.after
        def set_header(response: BaseResponse) -> None:
            response.headers.add("Foo", "FOO")

        return morepath.redirect("http://example.org")

    app.get_view.register(View(view), model=Model)

    model = Model()
    result = resolve_response(model, app().request(get_environ(path="")))
    assert result.status_code == 302
    assert result.headers.get("Location") == "http://example.org"
    assert result.headers.get("Foo") == "FOO"


def test_conditional_view_after() -> None:
    class app(morepath.App):
        pass

    dectate.commit(app)

    def view(self: object, request: morepath.Request) -> str:
        if False:

            @request.after  # type: ignore[unreachable]
            def set_header(response: Response) -> None:
                response.headers.add("Foo", "FOO")

        return "View!"

    app.get_view.register(View(view), model=Model)

    model = Model()
    result = resolve_response(model, app().request(get_environ(path="")))
    assert result.body == b"View!"
    assert result.headers.get("Foo") is None


def test_view_after_non_decorator() -> None:
    class app(morepath.App):
        pass

    dectate.commit(app)

    def set_header(response: Response) -> None:
        response.headers.add("Foo", "FOO")

    def view(self: object, request: morepath.Request) -> str:
        request.after(set_header)
        return "View!"

    app.get_view.register(View(view), model=Model)

    model = Model()
    result = resolve_response(model, app().request(get_environ(path="")))
    assert result.body == b"View!"
    assert result.headers.get("Foo") == "FOO"


def test_view_after_doesnt_apply_to_raised_404_exception() -> None:
    class App(morepath.App):
        pass

    class Root:
        pass

    @App.path(model=Root, path="")
    def get_root() -> Root:
        return Root()

    @App.view(model=Root)
    def view(self: Root, request: morepath.Request) -> None:
        @request.after
        def set_header(response: BaseResponse) -> None:
            response.headers.add("Foo", "FOO")

        raise HTTPNotFound()

    dectate.commit(App)

    c = Client(App())

    response = c.get("/", status=404)
    assert response.headers.get("Foo") is None


def test_view_after_doesnt_apply_to_returned_404_exception() -> None:
    class App(morepath.App):
        pass

    class Root:
        pass

    @App.path(model=Root, path="")
    def get_root() -> Root:
        return Root()

    @App.view(model=Root)
    def view(self: Root, request: morepath.Request) -> HTTPNotFound:
        @request.after
        def set_header(response: BaseResponse) -> None:
            response.headers.add("Foo", "FOO")

        return HTTPNotFound()

    dectate.commit(App)

    c = Client(App())

    response = c.get("/", status=404)
    assert response.headers.get("Foo") is None


@pytest.mark.parametrize(
    "status_code,exception_class", [(200, HTTPOk), (302, HTTPFound)]
)
def test_view_after_applies_to_some_exceptions(
    status_code: int, exception_class: type[Exception]
) -> None:
    class App(morepath.App):
        pass

    class Root:
        pass

    @App.path(model=Root, path="")
    def get_root() -> Root:
        return Root()

    @App.view(model=Root)
    def view(self: Root, request: morepath.Request) -> None:
        @request.after
        def set_header(response: BaseResponse) -> None:
            response.headers.add("Foo", "FOO")

        raise exception_class()

    dectate.commit(App)

    c = Client(App())

    response = c.get("/", status=status_code)
    assert response.headers.get("Foo") == "FOO"


def test_view_after_doesnt_apply_to_exception_view() -> None:
    class App(morepath.App):
        pass

    class Root:
        pass

    class MyException(Exception):
        pass

    @App.path(model=Root, path="")
    def get_root() -> Root:
        return Root()

    @App.view(model=Root)
    def view(self: Root, request: morepath.Request) -> None:
        @request.after
        def set_header(response: BaseResponse) -> None:
            response.headers.add("Foo", "FOO")

        raise MyException()

    @App.view(model=MyException)
    def exc_view(self: MyException, request: morepath.Request) -> str:
        return "My exception"

    dectate.commit(App)

    c = Client(App())

    response = c.get("/")
    assert response.body == b"My exception"
    assert response.headers.get("Foo") is None
