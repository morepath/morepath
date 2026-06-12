from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

import pytest

from morepath.app import App
from morepath.converter import Converter

if TYPE_CHECKING:
    from morepath.path import PathRegistry

    Info: TypeAlias = tuple[App, PathRegistry]


@pytest.fixture
def info() -> Info:
    class MyApp(App):
        pass

    MyApp.commit()

    app = MyApp()
    r = app.config.path_registry
    return app, r


def test_path_without_variables(info: Info) -> None:
    app, r = info

    class Foo:
        pass

    r.register_inverse_path(model=Foo, path="/", factory_args=set())
    path_info = app._get_path(Foo())
    assert path_info is not None
    assert path_info.path == ""
    assert path_info.parameters == {}


def test_path_with_variables(info: Info) -> None:
    app, r = info

    class Foo:
        def __init__(self, name: str) -> None:
            self.name = name

    r.register_path_variables(Foo, lambda obj: {"name": obj.name})
    r.register_inverse_path(
        model=Foo, path="/foos/{name}", factory_args={"name"}
    )
    path_info = app._get_path(Foo("a"))
    assert path_info is not None
    assert path_info.path == "foos/a"
    assert path_info.parameters == {}


def test_path_with_default_variables(info: Info) -> None:
    app, r = info

    class Foo:
        def __init__(self, name: str) -> None:
            self.name = name

    r.register_inverse_path(
        model=Foo, path="/foos/{name}", factory_args={"name"}
    )
    path_info = app._get_path(Foo("a"))
    assert path_info is not None
    assert path_info.path == "foos/a"
    assert path_info.parameters == {}


def test_path_with_parameters(info: Info) -> None:
    app, r = info

    class Foo:
        def __init__(self, name: str) -> None:
            self.name = name

    r.register_path_variables(Foo, lambda obj: {"name": obj.name})
    r.register_inverse_path(model=Foo, path="/foos", factory_args={"name"})
    path_info = app._get_path(Foo("a"))
    assert path_info is not None
    assert path_info.path == "foos"
    assert path_info.parameters == {"name": ["a"]}


def test_class_path_without_variables(info: Info) -> None:
    app, r = info

    class Foo:
        pass

    r.register_inverse_path(model=Foo, path="/", factory_args=set())
    path_info = app._class_path(Foo, {})
    assert path_info is not None
    assert path_info.path == ""
    assert path_info.parameters == {}


def test_class_path_with_variables(info: Info) -> None:
    app, r = info

    class Foo:
        def __init__(self, name: str) -> None:
            self.name = name

    r.register_inverse_path(
        model=Foo, path="/foos/{name}", factory_args={"name"}
    )
    path_info = app._class_path(Foo, {"name": "a"})
    assert path_info is not None
    assert path_info.path == "foos/a"
    assert path_info.parameters == {}


def test_class_path_with_parameters(info: Info) -> None:
    app, r = info

    class Foo:
        def __init__(self, name: str) -> None:
            self.name = name

    r.register_inverse_path(model=Foo, path="/foos", factory_args={"name"})
    path_info = app._class_path(Foo, {"name": "a"})
    assert path_info is not None
    assert path_info.path == "foos"
    assert path_info.parameters == {"name": ["a"]}


def test_class_path_variables_with_converters(info: Info) -> None:
    app, r = info

    class Foo:
        def __init__(self, value: int) -> None:
            self.value = value

    r.register_inverse_path(
        model=Foo,
        path="/foos/{value}",
        factory_args={"value"},
        converters={"value": Converter(int)},
    )
    path_info = app._class_path(Foo, {"value": 1})
    assert path_info is not None
    assert path_info.path == "foos/1"
    assert path_info.parameters == {}


def test_class_path_parameters_with_converters(info: Info) -> None:
    app, r = info

    class Foo:
        def __init__(self, value: int) -> None:
            self.value = value

    r.register_inverse_path(
        model=Foo,
        path="/foos",
        factory_args={"value"},
        converters={"value": Converter(int)},
    )
    path_info = app._class_path(Foo, {"value": 1})
    assert path_info is not None
    assert path_info.path == "foos"
    assert path_info.parameters == {"value": ["1"]}


def test_class_path_absorb(info: Info) -> None:
    app, r = info

    class Foo:
        pass

    r.register_inverse_path(
        model=Foo, path="/foos", factory_args=set(), absorb=True
    )
    path_info = app._class_path(Foo, {"absorb": "bar"})
    assert path_info is not None
    assert path_info.path == "foos/bar"
    assert path_info.parameters == {}


def test_class_path_extra_parameters(info: Info) -> None:
    app, r = info

    class Foo:
        pass

    r.register_inverse_path(model=Foo, path="/foos", factory_args=set())
    path_info = app._class_path(Foo, {"extra_parameters": {"a": "A", "b": "B"}})
    assert path_info is not None
    assert path_info.path == "foos"
    assert path_info.parameters == {"a": ["A"], "b": ["B"]}


def test_class_path_extra_parameters_convert(info: Info) -> None:
    app, r = info

    class Foo:
        pass

    r.register_inverse_path(
        model=Foo,
        path="/foos",
        factory_args=set(),
        converters={"a": Converter(int)},
    )
    path_info = app._class_path(Foo, {"extra_parameters": {"a": 1, "b": "B"}})
    assert path_info is not None
    assert path_info.path == "foos"
    assert path_info.parameters == {"a": ["1"], "b": ["B"]}
