from __future__ import annotations

from webtest import TestApp as Client

import morepath


def test_implicit_function() -> None:
    class App(morepath.App):
        @morepath.dispatch_method()
        def one(self) -> str:
            return "Default one"

        @morepath.dispatch_method()
        def two(self) -> str:
            return "Default two"

    @App.path(path="")
    class Model:
        def __init__(self) -> None:
            pass

    @App.method(App.one)
    def one_impl(self: App) -> str:
        return self.two()

    @App.method(App.two)
    def two_impl(self: App) -> str:
        return "The real two"

    @App.view(model=Model)
    def default(self: Model, request: morepath.Request[App]) -> str:
        return request.app.one()

    c = Client(App())

    response = c.get("/")
    assert response.body == b"The real two"


def test_implicit_function_mounted() -> None:
    class base(morepath.App):
        @morepath.dispatch_method()
        def one(self) -> str:
            return "Default one"

        @morepath.dispatch_method()
        def two(self) -> str:
            return "Default two"

    class alpha(base):
        pass

    class beta(base):
        def __init__(self, id: str) -> None:
            self.id = id

    @alpha.mount(path="mounted/{id}", app=beta)
    def mount_beta(id: str) -> beta:
        return beta(id=id)

    class AlphaRoot:
        pass

    class Root:
        def __init__(self, id: str) -> None:
            self.id = id

    @alpha.path(path="/", model=AlphaRoot)
    def get_alpha_root() -> AlphaRoot:
        return AlphaRoot()

    @beta.path(path="/", model=Root)
    def get_root(app: beta) -> Root:
        return Root(app.id)

    @beta.method(base.one)
    def one_impl(self: beta) -> str:
        return self.two()

    @beta.method(base.two)
    def two_impl(self: beta) -> str:
        return "The real two"

    @alpha.view(model=AlphaRoot)
    def alpha_default(self: AlphaRoot, request: morepath.Request[alpha]) -> str:
        return request.app.one()

    @beta.view(model=Root)
    def default(self: Root, request: morepath.Request[beta]) -> str:
        return f"View for {self.id}, message: {request.app.one()}"

    c = Client(alpha())

    response = c.get("/mounted/1")
    assert response.body == b"View for 1, message: The real two"

    response = c.get("/")
    assert response.body == b"Default one"
