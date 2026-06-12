from __future__ import annotations

from typing import Any

from webtest import TestApp as Client

import morepath


def test_json_obj_dump() -> None:
    class app(morepath.App):
        pass

    @app.path(path="/models/{x}")
    class Model:
        def __init__(self, x: str) -> None:
            self.x = x

    @app.json(model=Model)
    def default(self: Model, request: morepath.Request) -> Model:
        return self

    @app.dump_json(model=Model)
    def dump_model_json(
        self: Model, request: morepath.Request
    ) -> dict[str, Any]:
        return {"x": self.x}

    c = Client(app())

    response = c.get("/models/foo")
    assert response.json == {"x": "foo"}


def test_json_obj_dump_app_arg() -> None:
    class App(morepath.App):
        pass

    @App.path(path="/models/{x}")
    class Model:
        def __init__(self, x: str) -> None:
            self.x = x

    @App.json(model=Model)
    def default(self: Model, request: morepath.Request) -> Model:
        return self

    @App.dump_json(model=Model)
    def dump_model_json(
        app: App, obj: Model, request: morepath.Request
    ) -> dict[str, Any]:
        assert isinstance(app, App)
        return {"x": obj.x}

    c = Client(App())

    response = c.get("/models/foo")
    assert response.json == {"x": "foo"}
