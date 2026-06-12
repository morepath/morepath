from __future__ import annotations

from typing import Any

from webtest import TestApp as Client

import morepath


def test_function_extends() -> None:
    class App(morepath.App):
        @morepath.dispatch_method("obj")
        def foo(self, obj: Any) -> str:
            return "default"

    class Extending(App):
        pass

    class Alpha:
        pass

    @App.method(App.foo, obj=Alpha)
    def app_foo(app: App, obj: Alpha) -> str:
        return "App"

    @Extending.method(App.foo, obj=Alpha)
    def extending_foo(app: Extending, obj: Alpha) -> str:
        return "Extending"

    assert App().foo(Alpha()) == "App"
    assert Extending().foo(Alpha()) == "Extending"


def test_extends() -> None:
    class App(morepath.App):
        pass

    class Extending(App):
        pass

    @App.path(path="users/{username}")
    class User:
        def __init__(self, username: str) -> None:
            self.username = username

    @App.view(model=User)
    def render_user(self: User, request: morepath.Request) -> str:
        return "User: %s" % self.username

    @Extending.view(model=User, name="edit")
    def edit_user(self: User, request: morepath.Request) -> str:
        return "Edit user: %s" % self.username

    cl = Client(App())
    response = cl.get("/users/foo")
    assert response.body == b"User: foo"
    response = cl.get("/users/foo/edit", status=404)

    cl = Client(Extending())
    response = cl.get("/users/foo")
    assert response.body == b"User: foo"
    response = cl.get("/users/foo/edit")
    assert response.body == b"Edit user: foo"


def test_overrides_view() -> None:
    class App(morepath.App):
        pass

    class Overriding(App):
        pass

    @App.path(path="users/{username}")
    class User:
        def __init__(self, username: str) -> None:
            self.username = username

    @App.view(model=User)
    def render_user(self: User, request: morepath.Request) -> str:
        return "User: %s" % self.username

    @Overriding.view(model=User)
    def render_user2(self: User, request: morepath.Request) -> str:
        return "USER: %s" % self.username

    cl = Client(App())
    response = cl.get("/users/foo")
    assert response.body == b"User: foo"

    cl = Client(Overriding())
    response = cl.get("/users/foo")
    assert response.body == b"USER: foo"


def test_overrides_model() -> None:
    class App(morepath.App):
        pass

    class Overriding(App):
        pass

    @App.path(path="users/{username}")
    class User:
        def __init__(self, username: str) -> None:
            self.username = username

    @App.view(model=User)
    def render_user(self: User, request: morepath.Request) -> str:
        return "User: %s" % self.username

    @Overriding.path(model=User, path="users/{username}")
    def get_user(username: str) -> User | None:
        if username != "bar":
            return None
        return User(username)

    cl = Client(App())
    response = cl.get("/users/foo")
    assert response.body == b"User: foo"
    response = cl.get("/users/bar")
    assert response.body == b"User: bar"

    cl = Client(Overriding())
    response = cl.get("/users/foo", status=404)
    response = cl.get("/users/bar")
    assert response.body == b"User: bar"
