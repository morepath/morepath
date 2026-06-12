from __future__ import annotations

from typing import Any

import pytest
from webtest import TestApp as Client

import morepath


def test_load() -> None:
    class App(morepath.App):
        pass

    @App.path(path="/")
    class Root:
        pass

    def load(request: morepath.Request) -> Any:
        return request.json

    @App.view(model=Root, request_method="POST", load=load)
    def root_post(self: Root, request: morepath.Request, obj: Any) -> str:
        return "true" if obj == {"foo": "bar"} else "false"

    app = App()
    client = Client(app)

    r = client.post_json("/", {"foo": "bar"})

    assert r.body == b"true"


def test_load_requires_three_arguments() -> None:
    class App(morepath.App):
        pass

    @App.path(path="/")
    class Root:
        pass

    def load(request: morepath.Request) -> Any:
        return request.json

    @App.view(model=Root, request_method="POST", load=load)
    def root_post(self: Root, request: morepath.Request) -> None:
        pass

    app = App()
    app.commit()

    client = Client(app)

    with pytest.raises(TypeError):
        client.post_json("/", {"foo": "bar"})


def test_load_json() -> None:
    class App(morepath.App):
        pass

    @App.path(path="/")
    class Root:
        pass

    def load(request: morepath.Request) -> Any:
        return request.json

    @App.json(model=Root, request_method="POST", load=load)
    def root_post(self: Root, request: morepath.Request, obj: Any) -> str:
        return "true" if obj == {"foo": "bar"} else "false"

    app = App()
    client = Client(app)

    r = client.post_json("/", {"foo": "bar"})

    assert r.body == b'"true"'


def test_load_html() -> None:
    class App(morepath.App):
        pass

    @App.path(path="/")
    class Root:
        pass

    def load(request: morepath.Request) -> Any:
        return request.json

    @App.html(model=Root, request_method="POST", load=load)
    def root_post(self: Root, request: morepath.Request, obj: Any) -> str:
        return "true" if obj == {"foo": "bar"} else "false"

    app = App()
    client = Client(app)

    r = client.post_json("/", {"foo": "bar"})

    assert r.body == b"true"
