from __future__ import annotations

from typing import Any

from webtest import TestApp as Client

import morepath


def test_internal() -> None:
    class App(morepath.App):
        pass

    @App.path(path="")
    class Root:
        pass

    @App.json(model=Root)
    def root_default(self: Root, request: morepath.Request) -> dict[str, Any]:
        return {"internal": request.view(self, name="internal")}

    @App.json(model=Root, name="internal", internal=True)
    def root_internal(self: Root, request: morepath.Request) -> str:
        return "Internal!"

    c = Client(App())

    response = c.get("/")

    assert response.body == b'{"internal":"Internal!"}'

    c.get("/internal", status=404)
