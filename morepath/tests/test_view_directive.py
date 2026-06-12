from __future__ import annotations

import pytest
from webtest import TestApp as Client

import morepath
from dectate import ConflictError
from morepath.core import request_method_predicate
from reg import ClassIndex, KeyIndex


def test_view_get_only() -> None:
    class App(morepath.App):
        pass

    @App.path(path="")
    class Model:
        def __init__(self) -> None:
            pass

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View"

    c = Client(App())

    response = c.get("/")
    assert response.body == b"View"

    response = c.post("/", status=405)


def test_view_name_conflict_involving_default() -> None:
    class App(morepath.App):
        pass

    @App.path(path="")
    class Model:
        def __init__(self) -> None:
            pass

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View"

    @App.view(model=Model, name="")
    def default2(self: Model, request: morepath.Request) -> str:
        return "View"

    with pytest.raises(ConflictError):
        App.commit()


def test_view_custom_predicate_conflict_involving_default_extends() -> None:
    class Core(morepath.App):
        pass

    class App(Core):
        pass

    @Core.predicate(
        morepath.App.get_view,
        name="extra",
        default="DEFAULT",
        index=ClassIndex,
        after=request_method_predicate,
    )
    def dummy_predicate(request: morepath.Request) -> None:
        return None

    @App.path(path="")
    class Model:
        def __init__(self) -> None:
            pass

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return "View"

    @App.view(model=Model, extra="DEFAULT")
    def default2(self: Model, request: morepath.Request) -> str:
        return "View"

    with pytest.raises(ConflictError):
        App.commit()


def test_view_custom_predicate_without_fallback() -> None:
    class Core(morepath.App):
        pass

    class App(Core):
        pass

    @Core.predicate(
        morepath.App.get_view,
        name="extra",
        default="DEFAULT",
        index=KeyIndex,
        after=request_method_predicate,
    )
    def dummy_predicate(
        self: Core, obj: object, request: morepath.Request
    ) -> str:
        return "match"

    @App.path(path="")
    class Model:
        def __init__(self) -> None:
            pass

    @App.view(model=Model, extra="match")
    def default(self: Model, request: morepath.Request) -> str:
        return "View"

    @App.view(model=Model, name="foo", extra="not match")
    def not_match(self: Model, request: morepath.Request) -> str:
        return "Not match"

    c = Client(App())

    response = c.get("/")
    assert response.body == b"View"
    c.get("/foo", status=404)
