from __future__ import annotations

from typing import Any

from webtest import TestApp as Client

import morepath
from morepath.app import App
from reg import KeyIndex


def test_view_predicates() -> None:
    class app(App):
        pass

    @app.path(path="")
    class Root:
        pass

    @app.view(model=Root, name="foo", request_method="GET")
    def get(self: Root, request: morepath.Request) -> str:
        return "GET"

    @app.view(model=Root, name="foo", request_method="POST")
    def post(self: Root, request: morepath.Request) -> str:
        return "POST"

    c = Client(app())

    response = c.get("/foo")
    assert response.body == b"GET"
    response = c.post("/foo")
    assert response.body == b"POST"


def test_extra_predicates() -> None:
    class app(App):
        pass

    @app.path(path="{id}")
    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @app.view(model=Model, name="foo", id="a")
    def get_a(self: Model, request: morepath.Request) -> str:
        return "a"

    @app.view(model=Model, name="foo", id="b")
    def get_b(self: Model, request: morepath.Request) -> str:
        return "b"

    @app.predicate(
        morepath.App.get_view,
        name="id",
        default="",
        index=KeyIndex,
        after=morepath.request_method_predicate,
    )
    def id_predicate(self: app, obj: Any, request: morepath.Request) -> Any:
        return obj.id

    c = Client(app())

    response = c.get("/a/foo")
    assert response.body == b"a"
    response = c.get("/b/foo")
    assert response.body == b"b"
