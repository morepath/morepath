from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from webtest import TestApp as Client

import dectate
import morepath
import reg
from dectate import ConflictError, DirectiveReportError
from morepath.converter import Converter
from morepath.error import LinkError
from morepath.view import render_html

from .fixtures import (
    abbr,
    basic,
    conflict,
    mapply_bug,
    method,
    nested,
    noconverter,
)

if TYPE_CHECKING:
    from webob import Response as BaseResponse


def test_basic() -> None:
    c = Client(basic.app())

    response = c.get("/foo")

    assert response.body == b"The view for model: foo"

    response = c.get("/foo/link")
    assert response.body == b"http://localhost/foo"


def test_basic_json() -> None:
    c = Client(basic.app())

    response = c.get("/foo/json")

    assert response.body == b'{"id":"foo"}'


def test_basic_root() -> None:
    c = Client(basic.app())

    response = c.get("/")

    assert response.body == b"The root: ROOT"

    # + is to make sure we get the view, not the sub-model as
    # the model is greedy
    response = c.get("/+link")
    assert response.body == b"http://localhost/"


def test_nested() -> None:
    c = Client(nested.outer_app())

    response = c.get("/inner/foo")

    assert response.body == b"The view for model: foo"

    response = c.get("/inner/foo/link")
    assert response.body == b"http://localhost/inner/foo"


def test_abbr() -> None:
    c = Client(abbr.app())

    response = c.get("/foo")
    assert response.body == b"Default view: foo"

    response = c.get("/foo/edit")
    assert response.body == b"Edit view: foo"


def test_scanned_static_method() -> None:
    c = Client(method.app())

    response = c.get("/static")
    assert response.body == b"Static Method"

    root = method.Root()
    assert isinstance(root.static_method(), method.StaticMethod)


def test_scanned_no_converter() -> None:
    with pytest.raises(DirectiveReportError):
        noconverter.app.commit()


def test_scanned_conflict() -> None:
    with pytest.raises(ConflictError):
        conflict.app.commit()


def test_basic_scenario() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        def __init__(self) -> None:
            self.value = "ROOT"

    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @app.path(model=Model, path="{id}")
    def get_model(id: str) -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "The view for model: %s" % self.id

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    @app.view(model=Model, name="json", render=morepath.render_json)
    def json(self: Model, request: morepath.Request) -> dict[str, Any]:
        return {"id": self.id}

    @app.view(model=Root)
    def root_default(self: Root, request: morepath.Request) -> str:
        return "The root: %s" % self.value

    @app.view(model=Root, name="link")
    def root_link(self: Root, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/foo")
    assert response.body == b"The view for model: foo"

    response = c.get("/foo/link")
    assert response.body == b"http://localhost/foo"

    response = c.get("/foo/json")
    assert response.body == b'{"id":"foo"}'

    response = c.get("/")
    assert response.body == b"The root: ROOT"

    # + is to make sure we get the view, not the sub-model
    response = c.get("/+link")
    assert response.body == b"http://localhost/"


def test_link_to_unknown_model() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        def __init__(self) -> None:
            self.value = "ROOT"

    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @app.view(model=Root)
    def root_link(self: Root, request: morepath.Request) -> str:
        try:
            return request.link(Model("foo"))
        except LinkError:
            return "Link error"

    @app.view(model=Root, name="default")
    def root_link_with_default(self: Root, request: morepath.Request) -> str:
        try:
            return request.link(Model("foo"), default="hey")
        except LinkError:
            return "Link Error"

    c = Client(app())

    response = c.get("/")
    assert response.body == b"Link error"
    response = c.get("/default")
    assert response.body == b"Link Error"


def test_link_to_none() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        def __init__(self) -> None:
            self.value = "ROOT"

    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @app.view(model=Root)
    def root_link(self: Root, request: morepath.Request) -> str:
        return str(request.link(None) is None)

    @app.view(model=Root, name="default")
    def root_link_with_default(self: Root, request: morepath.Request) -> str:
        return request.link(None, default="unknown")

    c = Client(app())

    response = c.get("/")
    assert response.body == b"True"
    response = c.get("/default")
    assert response.body == b"unknown"


def test_link_with_parameters() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        def __init__(self) -> None:
            self.value = "ROOT"

    class Model:
        def __init__(self, id: str, param: int) -> None:
            self.id = id
            self.param = param

    @app.path(model=Model, path="{id}")
    def get_model(id: str, param: int = 0) -> Model:
        assert isinstance(param, int)
        return Model(id, param)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return f"The view for model: {self.id} {self.param}"

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/foo")
    assert response.body == b"The view for model: foo 0"

    response = c.get("/foo/link")
    assert response.body == b"http://localhost/foo?param=0"

    response = c.get("/foo?param=1")
    assert response.body == b"The view for model: foo 1"

    response = c.get("/foo/link?param=1")
    assert response.body == b"http://localhost/foo?param=1"


def test_root_link_with_parameters() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        def __init__(self, param: int = 0) -> None:
            assert isinstance(param, int)
            self.param = param

    @app.view(model=Root)
    def default(self: Root, request: morepath.Request) -> str:
        return "The view for root: %s" % self.param

    @app.view(model=Root, name="link")
    def link(self: Root, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/")
    assert response.body == b"The view for root: 0"

    response = c.get("/link")
    assert response.body == b"http://localhost/?param=0"

    response = c.get("/?param=1")
    assert response.body == b"The view for root: 1"

    response = c.get("/link?param=1")
    assert response.body == b"http://localhost/?param=1"


def test_link_with_prefix() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        pass

    @app.view(model=Root, name="link")
    def link(self: Root, request: morepath.Request) -> str:
        return request.link(self)

    @app.link_prefix()
    def link_prefix(request: morepath.Request) -> str:
        return request.headers["TESTPREFIX"]

    c = Client(app())

    # we don't do anything with the prefix, so a slash at the end of the prefix
    # leads to a double prefix at the end
    response = c.get("/link", headers={"TESTPREFIX": "http://testhost/"})
    assert response.body == b"http://testhost//"

    response = c.get("/link", headers={"TESTPREFIX": "http://testhost"})
    assert response.body == b"http://testhost/"


def test_link_with_prefix_app_arg() -> None:
    class App(morepath.App):
        pass

    @App.path(path="")
    class Root:
        pass

    @App.view(model=Root, name="link")
    def link(self: Root, request: morepath.Request) -> str:
        return request.link(self)

    @App.link_prefix()
    def link_prefix(app: App, request: morepath.Request) -> str:
        assert isinstance(app, App)
        return request.headers["TESTPREFIX"]

    c = Client(App())

    # we don't do anything with the prefix, so a slash at the end of the prefix
    # leads to a double prefix at the end
    response = c.get("/link", headers={"TESTPREFIX": "http://testhost/"})
    assert response.body == b"http://testhost//"

    response = c.get("/link", headers={"TESTPREFIX": "http://testhost"})
    assert response.body == b"http://testhost/"


def test_link_prefix_cache() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        pass

    @app.view(model=Root, name="link")
    def link(self: Root, request: morepath.Request) -> str:
        request.link(self)  # make an extra call before returning
        return request.link(self)

    @app.link_prefix()
    def link_prefix(request: morepath.Request) -> str:
        if not hasattr(request, "callnumber"):
            request.callnumber = 1  # type: ignore[attr-defined]
        else:
            request.callnumber += 1  # pyright: ignore
        return str(request.callnumber)  # type: ignore[attr-defined]

    c = Client(app())

    response = c.get("/link")
    assert response.body == b"1/"


def test_link_with_invalid_prefix() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        pass

    @app.view(model=Root, name="link")
    def link(self: Root, request: morepath.Request) -> str:
        return request.link(self)

    @app.link_prefix()
    def link_prefix(request: morepath.Request) -> None:
        return None

    c = Client(app())

    with pytest.raises(TypeError):
        c.get("/link")


def test_external_link_prefix() -> None:
    class App(morepath.App):
        pass

    class ExternalApp(morepath.App):
        pass

    class InternalDoc:
        pass

    class ExternalDoc:
        pass

    @App.path(model=InternalDoc, path="")
    def internal_path(request: morepath.Request) -> InternalDoc:
        return InternalDoc()

    @ExternalApp.path(model=ExternalDoc, path="external")
    def external_path(request: morepath.Request) -> ExternalDoc:
        return ExternalDoc()

    @App.defer_links(model=ExternalDoc)
    def defer_external_links(app: App, obj: ExternalDoc) -> ExternalApp:
        return ExternalApp()

    @ExternalApp.link_prefix()
    def prefix_external_link(request: morepath.Request) -> str:
        return "example.org"

    @App.json(model=InternalDoc)
    def main_view(
        self: InternalDoc, request: morepath.Request
    ) -> dict[str, Any]:
        return {
            "internal_link": request.link(InternalDoc()),
            "external_link_def": request.link(ExternalDoc()),
            "external_link_expl": request.link(
                ExternalDoc(), app=ExternalApp()
            ),
        }

    assert Client(App()).get("/").json == {
        "external_link_expl": "example.org/external",
        "external_link_def": "example.org/external",
        "internal_link": "http://localhost/",
    }


def test_implicit_variables() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        pass

    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @app.path(model=Model, path="{id}")
    def get_model(id: str) -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "The view for model: %s" % self.id

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/foo/link")
    assert response.body == b"http://localhost/foo"


def test_implicit_parameters() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        pass

    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @app.path(model=Model, path="foo")
    def get_model(id: str) -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "The view for model: %s" % self.id

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/foo")
    assert response.body == b"The view for model: None"
    response = c.get("/foo?id=bar")
    assert response.body == b"The view for model: bar"
    response = c.get("/foo/link")
    assert response.body == b"http://localhost/foo"
    response = c.get("/foo/link?id=bar")
    assert response.body == b"http://localhost/foo?id=bar"


def test_implicit_parameters_default() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        pass

    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @app.path(model=Model, path="foo")
    def get_model(id: str = "default") -> Model:
        return Model(id)

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "The view for model: %s" % self.id

    @app.view(model=Model, name="link")
    def link(self: Model, request: morepath.Request) -> str:
        return request.link(self)

    c = Client(app())

    response = c.get("/foo")
    assert response.body == b"The view for model: default"
    response = c.get("/foo?id=bar")
    assert response.body == b"The view for model: bar"
    response = c.get("/foo/link")
    assert response.body == b"http://localhost/foo?id=default"
    response = c.get("/foo/link?id=bar")
    assert response.body == b"http://localhost/foo?id=bar"


def test_simple_root() -> None:
    class app(morepath.App):
        pass

    class Hello:
        pass

    hello = Hello()

    @app.path(model=Hello, path="")
    def hello_model() -> Hello:
        return hello

    @app.view(model=Hello)
    def hello_view(self: Hello, request: morepath.Request) -> str:
        return "hello"

    c = Client(app())

    response = c.get("/")
    assert response.body == b"hello"


def test_json_directive() -> None:
    class app(morepath.App):
        pass

    @app.path(path="{id}")
    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @app.json(model=Model)
    def json(self: Model, request: morepath.Request) -> dict[str, Any]:
        return {"id": self.id}

    c = Client(app())

    response = c.get("/foo")
    assert response.body == b'{"id":"foo"}'


def test_redirect() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        def __init__(self) -> None:
            pass

    @app.view(model=Root, render=render_html)
    def default(self: Root, request: morepath.Request) -> BaseResponse:
        return morepath.redirect("/")

    c = Client(app())

    c.get("/", status=302)


def test_root_conflict() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        pass

    @app.path(path="")
    class Something:
        pass

    with pytest.raises(ConflictError):
        app.commit()


def test_root_conflict2() -> None:
    class app(morepath.App):
        pass

    @app.path(path="")
    class Root:
        pass

    @app.path(path="/")
    class Something:
        pass

    with pytest.raises(ConflictError):
        app.commit()


def test_root_no_conflict_different_apps() -> None:
    class app_a(morepath.App):
        pass

    class app_b(morepath.App):
        pass

    @app_a.path(path="")
    class Root:
        pass

    @app_b.path(path="")
    class Something:
        pass

    dectate.commit(app_a, app_b)


def test_model_conflict() -> None:
    class app(morepath.App):
        pass

    class A:
        pass

    @app.path(model=A, path="a")
    def get_a() -> A:
        return A()

    @app.path(model=A, path="a")
    def get_a_again() -> A:
        return A()

    with pytest.raises(ConflictError):
        app.commit()


def test_path_conflict() -> None:
    class app(morepath.App):
        pass

    class A:
        pass

    class B:
        pass

    @app.path(model=A, path="a")
    def get_a() -> A:
        return A()

    @app.path(model=B, path="a")
    def get_b() -> B:
        return B()

    with pytest.raises(ConflictError):
        app.commit()


def test_path_conflict_with_variable() -> None:
    class app(morepath.App):
        pass

    class A:
        pass

    class B:
        pass

    @app.path(model=A, path="a/{id}")
    def get_a(id: str) -> A:
        return A()

    @app.path(model=B, path="a/{id2}")
    def get_b(id2: str) -> B:
        return B()

    with pytest.raises(ConflictError):
        app.commit()


def test_path_conflict_with_variable_different_converters() -> None:
    class app(morepath.App):
        pass

    class A:
        pass

    class B:
        pass

    @app.path(model=A, path="a/{id}", converters={"id": Converter(decode=int)})
    def get_a(id: int) -> A:
        return A()

    @app.path(model=B, path="a/{id}")
    def get_b(id: str) -> B:
        return B()

    with pytest.raises(ConflictError):
        app.commit()


def test_model_no_conflict_different_apps() -> None:
    class app_a(morepath.App):
        pass

    class app_b(morepath.App):
        pass

    class A:
        pass

    @app_a.path(model=A, path="a")
    def get_a() -> A:
        return A()

    @app_b.path(model=A, path="a")
    def get_a_again() -> A:
        return A()

    dectate.commit(app_a, app_b)


def test_view_conflict() -> None:
    class app(morepath.App):
        pass

    class Model:
        pass

    @app.view(model=Model, name="a")
    def a_view(self: Model, request: morepath.Request) -> None:
        pass

    @app.view(model=Model, name="a")
    def a1_view(self: Model, request: morepath.Request) -> None:
        pass

    with pytest.raises(ConflictError):
        app.commit()


def test_view_no_conflict_different_names() -> None:
    class app(morepath.App):
        pass

    class Model:
        pass

    @app.view(model=Model, name="a")
    def a_view(self: Model, request: morepath.Request) -> None:
        pass

    @app.view(model=Model, name="b")
    def b_view(self: Model, request: morepath.Request) -> None:
        pass

    app.commit()


def test_view_no_conflict_different_predicates() -> None:
    class app(morepath.App):
        pass

    class Model:
        pass

    @app.view(model=Model, name="a", request_method="GET")
    def a_view(self: Model, request: morepath.Request) -> None:
        pass

    @app.view(model=Model, name="a", request_method="POST")
    def b_view(self: Model, request: morepath.Request) -> None:
        pass

    app.commit()


def test_view_no_conflict_different_apps() -> None:
    class app_a(morepath.App):
        pass

    class app_b(morepath.App):
        pass

    class Model:
        pass

    @app_a.view(model=Model, name="a")
    def a_view(self: Model, request: morepath.Request) -> None:
        pass

    @app_b.view(model=Model, name="a")
    def a1_view(self: Model, request: morepath.Request) -> None:
        pass

    dectate.commit(app_a, app_b)


def test_view_conflict_with_json() -> None:
    class app(morepath.App):
        pass

    class Model:
        pass

    @app.view(model=Model, name="a")
    def a_view(self: Model, request: morepath.Request) -> None:
        pass

    @app.json(model=Model, name="a")
    def a1_view(self: Model, request: morepath.Request) -> None:
        pass

    with pytest.raises(ConflictError):
        app.commit()


def test_view_conflict_with_html() -> None:
    class app(morepath.App):
        pass

    class Model:
        pass

    @app.view(model=Model, name="a")
    def a_view(self: Model, request: morepath.Request) -> None:
        pass

    @app.html(model=Model, name="a")
    def a1_view(self: Model, request: morepath.Request) -> None:
        pass

    with pytest.raises(ConflictError):
        app.commit()


def test_function() -> None:
    class App(morepath.App):
        @morepath.dispatch_method("a")
        def func(self, a: Any) -> str:
            return "default"

    class A:
        pass

    @App.method(App.func, a=A)
    def a_func(app: App, request: morepath.Request) -> str:
        return "A"

    app = App()
    assert app.func(A()) == "A"
    assert app.func(None) == "default"


def test_method() -> None:
    class App(morepath.App):
        @morepath.dispatch_method("a")
        def func(self, a: Any) -> str:
            return "default"

    class A:
        pass

    @App.method(App.func, a=A)
    def a_func(app: App, request: morepath.Request) -> str:
        assert isinstance(app, App)
        return "A"

    app = App()
    assert app.func(A()) == "A"
    assert app.func(None) == "default"


def test_function_conflict() -> None:
    class app(morepath.App):
        @morepath.dispatch_method("a")
        def func(self, a: Any) -> None:
            pass

    class A:
        pass

    @app.method(app.func, a=A)
    def a_func(app: app, a: A, request: morepath.Request) -> None:
        pass

    @app.method(app.func, a=A)
    def a1_func(app: app, a: A, request: morepath.Request) -> None:
        pass

    with pytest.raises(ConflictError):
        app.commit()


def test_function_no_conflict_different_apps() -> None:
    class base(morepath.App):
        @morepath.dispatch_method("a")
        def func(self, a: Any) -> None:
            pass

    class app_a(base):
        pass

    class app_b(base):
        pass

    class A:
        pass

    @app_a.method(base.func, a=A)
    def a_func(app: app_a, a: A) -> None:
        pass

    @app_b.method(base.func, a=A)
    def a1_func(app: app_b, a: A) -> None:
        pass

    dectate.commit(app_a, app_b)


def test_run_app_with_context_without_it() -> None:
    class app(morepath.App):

        def __init__(self, mount_id: str) -> None:
            self.mount_id = mount_id

    with pytest.raises(TypeError):
        app()  # type: ignore


def test_mapply_bug() -> None:
    c = Client(mapply_bug.app())

    response = c.get("/")

    assert response.body == b"the root"


def test_abbr_imperative() -> None:
    class app(morepath.App):
        pass

    class Model:
        pass

    @app.path(path="/", model=Model)
    def get_model() -> Model:
        return Model()

    with app.view(model=Model) as view:

        @view()
        def default(self: Model, request: morepath.Request) -> str:
            return "Default view"

        @view(name="edit")
        def edit(self: Model, request: morepath.Request) -> str:
            return "Edit view"

    c = Client(app())

    response = c.get("/")
    assert response.body == b"Default view"

    response = c.get("/edit")
    assert response.body == b"Edit view"


def test_abbr_partial_imperative() -> None:
    class app(morepath.App):
        pass

    class Model:
        pass

    @app.path(path="/", model=Model)
    def get_model() -> Model:
        return Model()

    with app.view.partial(model=Model) as view:

        @view()
        def default(self: Model, request: morepath.Request) -> str:
            return "Default view"

        @view(name="edit")
        def edit(self: Model, request: morepath.Request) -> str:
            return "Edit view"

    c = Client(app())

    response = c.get("/")
    assert response.body == b"Default view"

    response = c.get("/edit")
    assert response.body == b"Edit view"


def test_abbr_exception() -> None:
    class app(morepath.App):
        pass

    class Model:
        pass

    @app.path(path="/", model=Model)
    def get_model() -> Model:
        return Model()

    try:
        with app.view(model=Model) as view:

            @view()
            def default(self: Model, request: morepath.Request) -> str:
                return "Default view"

            _ = 1 / 0

            @view(name="edit")
            def edit(self: Model, request: morepath.Request) -> str:
                return "Edit view"

    except ZeroDivisionError:
        pass

    c = Client(app())

    response = c.get("/")
    assert response.body == b"Default view"

    # an exception happened halfway, so this one is never registered
    c.get("/edit", status=404)


def test_abbr_imperative2() -> None:
    class app(morepath.App):
        pass

    class Model:
        pass

    @app.path(path="/", model=Model)
    def get_model() -> Model:
        return Model()

    with app.view(model=Model) as view:

        @view()
        def default(self: Model, request: morepath.Request) -> str:
            return "Default view"

        @view(name="edit")
        def edit(self: Model, request: morepath.Request) -> str:
            return "Edit view"

    c = Client(app())

    response = c.get("/")
    assert response.body == b"Default view"

    response = c.get("/edit")
    assert response.body == b"Edit view"


def test_abbr_nested() -> None:
    class app(morepath.App):
        pass

    class Model:
        pass

    @app.path(path="/", model=Model)
    def get_model() -> Model:
        return Model()

    with app.view(model=Model) as view:

        @view()
        def default(self: Model, request: morepath.Request) -> str:
            return "Default"

        with view(name="extra") as view:

            @view()
            def get(self: Model, request: morepath.Request) -> str:
                return "Get"

            @view(request_method="POST")
            def post(self: Model, request: morepath.Request) -> str:
                return "Post"

    c = Client(app())

    response = c.get("/")
    assert response.body == b"Default"

    response = c.get("/extra")
    assert response.body == b"Get"

    response = c.post("/extra")
    assert response.body == b"Post"


def test_function_directive() -> None:
    class app(morepath.App):
        @morepath.dispatch_method("o")
        def mygeneric(self, o: Any) -> str:
            return "The object: %s" % o

    class Foo:
        def __init__(self, value: int) -> None:
            self.value = value

        def __repr__(self) -> str:
            return "<Foo with value: %s>" % self.value

    @app.method(app.mygeneric, o=Foo)
    def mygeneric_for_foo(app: app, o: Foo) -> str:
        return "The foo object: %s" % o

    a = app()

    assert a.mygeneric("blah") == "The object: blah"
    assert a.mygeneric(Foo(1)) == ("The foo object: <Foo with value: 1>")


def test_classgeneric_function_directive() -> None:
    class app(morepath.App):
        @morepath.dispatch_method(reg.match_class("o"))
        def mygeneric(self, o: Any) -> str:
            return "The object"

    class Foo:
        pass

    @app.method(app.mygeneric, o=Foo)
    def mygeneric_for_foo(app: app, o: Foo) -> str:
        return "The foo object"

    a = app()

    assert a.mygeneric(object) == "The object"
    assert a.mygeneric(Foo) == "The foo object"


def test_staticmethod() -> None:
    class App(morepath.App):
        pass

    @App.path("/")
    class Root:
        pass

    class A:
        @staticmethod
        @App.view(model=Root)
        def root_default(
            self: Root,  # pyright: ignore[reportSelfClsParameterName]
            request: morepath.Request,
        ) -> str:
            assert isinstance(self, Root)
            return "Hello world"

    c = Client(App())

    response = c.get("/")
    assert response.body == b"Hello world"


def test_classmethod_equivalent_to_staticmethod() -> None:
    class App(morepath.App):
        pass

    @App.path("/")
    class Root:
        pass

    class A:
        @classmethod
        @App.view(model=Root)
        def root_default(
            self: Any,  # pyright: ignore[reportSelfClsParameterName]
            request: morepath.Request,
        ) -> str:
            assert isinstance(self, Root)
            return "Hello world"

    c = Client(App())

    response = c.get("/")
    assert response.body == b"Hello world"


def test_classmethod_bound_outside() -> None:
    class App(morepath.App):
        pass

    @App.path("/")
    class Root:
        pass

    class A:
        @classmethod
        def root_default(cls, self: Root, request: morepath.Request) -> str:
            assert isinstance(self, Root)
            return "Hello world"

    App.view(model=Root)(A.root_default)

    c = Client(App())

    response = c.get("/")
    assert response.body == b"Hello world"


def test_instantiation_before_config() -> None:
    class App(morepath.App):
        pass

    # Typically, instantiating App would be done later, after the
    # decorators.  Since this use case has been found in the wild, we
    # might as well make sure it works:
    app = App()

    @App.path(path="")
    class Hello:
        pass

    @App.view(model=Hello)
    def hello_view(self: App, request: morepath.Request) -> str:
        return "hello"

    c = Client(app)

    response = c.get("/")
    assert response.body == b"hello"
