from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import webob

import dectate
import morepath
from morepath.converter import IDENTITY_CONVERTER, Converter, ConverterRegistry
from morepath.path import get_arguments


def consume(
    mount: morepath.App, path: str, parameters: Any = None
) -> tuple[Any, morepath.Request]:
    if parameters:
        path += "?" + urlencode(parameters, True)
    request = mount.request(webob.Request.blank(path).environ)
    return mount.config.path_registry.consume(request), request


class Root:
    pass


class Model:
    id: str
    param: str


def root_variables(_root: Root) -> dict[str, Any]:
    return {}


def model_variables(model: Model) -> dict[str, str]:
    return {"id": model.id}


def model_variables_with_param(model: Model) -> dict[str, str]:
    return {"id": model.id, "param": model.param}


def test_register_path() -> None:
    class App(morepath.App):
        pass

    root = Root()

    def get_model(id: str) -> Model:
        model = Model()
        model.id = id
        return model

    dectate.commit(App)

    path_registry = App.config.path_registry

    path_registry.register_path(
        Root, "", root_variables, None, None, None, False, None, lambda: root
    )
    path_registry.register_path(
        Model,
        "{id}",
        model_variables,
        None,
        None,
        None,
        False,
        None,
        get_model,
    )

    app = App()

    obj, _request = consume(app, "a")
    assert obj.id == "a"
    model = Model()
    model.id = "b"

    info = app._get_path(model)
    assert info is not None
    assert info.path == "b"
    assert info.parameters == {}


def test_register_path_with_parameters() -> None:
    class App(morepath.App):
        pass

    root = Root()

    def get_model(id: str, param: str = "default") -> Model:
        model = Model()
        model.id = id
        model.param = param
        return model

    dectate.commit(App)

    path_registry = App.config.path_registry

    path_registry.register_path(
        Root, "", root_variables, None, None, None, False, None, lambda: root
    )
    path_registry.register_path(
        Model,
        "{id}",
        model_variables_with_param,
        None,
        None,
        None,
        False,
        None,
        get_model,
    )

    mount = App()

    obj, _request = consume(mount, "a")
    assert obj.id == "a"
    assert obj.param == "default"

    obj, _request = consume(mount, "a", {"param": "value"})
    assert obj.id == "a"
    assert obj.param == "value"

    model = Model()
    model.id = "b"
    model.param = "other"

    info = mount._get_path(model)
    assert info is not None
    assert info.path == "b"
    assert info.parameters == {"param": ["other"]}


def test_traject_path_with_leading_slash() -> None:
    class App(morepath.App):
        pass

    root = Root()

    def get_model(id: str) -> Model:
        model = Model()
        model.id = id
        return model

    dectate.commit(App)

    path_registry = App.config.path_registry

    path_registry.register_path(
        Root, "", root_variables, None, None, None, False, None, lambda: root
    )
    path_registry.register_path(
        Model,
        "/foo/{id}",
        model_variables,
        None,
        None,
        None,
        False,
        None,
        get_model,
    )

    mount = App()
    obj, _request = consume(mount, "foo/a")
    assert obj.id == "a"
    obj, _request = consume(mount, "/foo/a")
    assert obj.id == "a"


def test_get_arguments() -> None:
    def foo(a: int, b: int) -> None:
        pass

    assert get_arguments(foo, []) == {"a": None, "b": None}


def test_get_arguments_defaults() -> None:
    def foo(a: int, b: int = 1) -> None:
        pass

    assert get_arguments(foo, []) == {"a": None, "b": 1}


def test_get_arguments_exclude() -> None:
    def foo(a: int, b: int, request: morepath.Request) -> None:
        pass

    assert get_arguments(foo, ["request"]) == {"a": None, "b": None}


def test_argument_and_explicit_converters_none_defaults() -> None:
    reg = ConverterRegistry()

    assert reg.argument_and_explicit_converters({"a": None}, {}) == {
        "a": IDENTITY_CONVERTER
    }


def test_argument_and_explicit_converters_explicit() -> None:
    reg = ConverterRegistry()

    assert reg.argument_and_explicit_converters({"a": None}, {"a": Converter(int)}) == {
        "a": Converter(int)
    }


def test_argument_and_explicit_converters_from_type() -> None:

    reg = ConverterRegistry()
    reg.register_converter(int, Converter(int))

    assert reg.argument_and_explicit_converters({"a": None}, {"a": int}) == {
        "a": Converter(int)
    }
