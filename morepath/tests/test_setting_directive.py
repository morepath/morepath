from __future__ import annotations

import pytest
from webtest import TestApp as Client

import dectate
import morepath
from morepath.error import ConflictError


def test_settings_property() -> None:
    class App(morepath.App):
        pass

    @App.setting("foo", "bar")
    def get_foo_setting() -> str:
        return "bar"

    dectate.commit(App)
    app = App()

    assert app.settings is app.config.setting_registry


def test_app_extends_settings() -> None:
    class alpha(morepath.App):
        pass

    class beta(alpha):
        pass

    @alpha.setting("one", "foo")
    def get_foo_setting() -> str:
        return "FOO"

    @beta.setting("one", "bar")
    def get_bar_setting() -> str:
        return "BAR"

    dectate.commit(alpha, beta)

    alpha_inst = alpha()

    settings = alpha_inst.config.setting_registry

    assert settings.one.foo == "FOO"
    with pytest.raises(AttributeError):
        settings.one.bar

    beta_inst = beta()
    settings = beta_inst.config.setting_registry

    assert settings.one.foo == "FOO"
    assert settings.one.bar == "BAR"


def test_app_overrides_settings() -> None:
    class alpha(morepath.App):
        pass

    class beta(alpha):
        pass

    @alpha.setting("one", "foo")
    def get_foo_setting() -> str:
        return "FOO"

    @beta.setting("one", "foo")
    def get_bar_setting() -> str:
        return "OVERRIDE"

    dectate.commit(alpha, beta)

    assert alpha().config.setting_registry.one.foo == "FOO"
    assert beta().config.setting_registry.one.foo == "OVERRIDE"


def test_app_overrides_settings_three() -> None:
    class alpha(morepath.App):
        pass

    class beta(alpha):
        pass

    class gamma(beta):
        pass

    @alpha.setting("one", "foo")
    def get_foo_setting() -> str:
        return "FOO"

    @beta.setting("one", "foo")
    def get_bar_setting() -> str:
        return "OVERRIDE"

    dectate.commit(alpha, beta, gamma)

    assert gamma().config.setting_registry.one.foo == "OVERRIDE"


def test_app_section_settings() -> None:
    class app(morepath.App):
        pass

    @app.setting_section("one")
    def settings() -> dict[str, str]:
        return {"foo": "FOO", "bar": "BAR"}

    dectate.commit(app)

    app_inst = app()

    s = app_inst.config.setting_registry

    assert s.one.foo == "FOO"
    assert s.one.bar == "BAR"


def test_app_section_settings_conflict() -> None:
    class app(morepath.App):
        pass

    @app.setting_section("one")
    def settings() -> dict[str, str]:
        return {"foo": "FOO", "bar": "BAR"}

    @app.setting("one", "foo")
    def get_foo() -> str:
        return "another"

    with pytest.raises(ConflictError):
        dectate.commit(app)


def test_settings_property_in_view() -> None:
    class app(morepath.App):
        pass

    @app.setting("section", "name")
    def setting() -> str:
        return "LAH"

    @app.path(path="")
    class Model:
        def __init__(self) -> None:
            pass

    @app.view(model=Model)
    def default(self: Model, request: morepath.Request) -> str:
        return request.app.settings.section.name  # type: ignore[no-any-return]

    c = Client(app())

    response = c.get("/")
    assert response.body == b"LAH"
