from __future__ import annotations

from typing import Any

import morepath
from reg import ClassIndex, KeyIndex


def test_dispatch_method_directive() -> None:
    class App(morepath.App):
        @morepath.dispatch_method("obj")
        def f(self, obj: Any) -> str:
            return "fallback"

    class Foo:
        pass

    class Bar:
        pass

    class Other:
        pass

    @App.method(App.f, obj=Foo)
    def f_foo(self: App, obj: Foo) -> str:
        return "foo"

    @App.method(App.f, obj=Bar)
    def f_bar(self: App, obj: Bar) -> str:
        return "bar"

    a = App()

    assert a.f(Foo()) == "foo"
    assert a.f(Bar()) == "bar"
    assert a.f(Other()) == "fallback"


def test_dispatch_function_directive() -> None:
    class App(morepath.App):
        @morepath.dispatch_method("obj")
        def f(self, obj: Any) -> str:
            return "fallback"

    class Foo:
        pass

    class Bar:
        pass

    class Other:
        pass

    @App.method(App.f, obj=Foo)
    def f_foo(app: App, obj: Foo) -> str:
        return "foo"

    @App.method(App.f, obj=Bar)
    def f_bar(app: App, obj: Bar) -> str:
        return "bar"

    a = App()

    assert a.f(Foo()) == "foo"
    assert a.f(Bar()) == "bar"
    assert a.f(Other()) == "fallback"


def test_dispatch_external_predicates() -> None:
    class App(morepath.App):
        @morepath.dispatch_method()
        def f(app, obj: Any) -> str:
            return "fallback"

    class Foo:
        pass

    class Bar:
        pass

    class Other:
        pass

    @App.predicate(App.f, name="model", default=None, index=ClassIndex)
    def f_obj(app: App, obj: object) -> type[Any]:
        return obj.__class__

    @App.method(App.f, model=Foo)
    def f_foo(app: App, obj: Foo) -> str:
        return "foo"

    @App.method(App.f, model=Bar)
    def f_bar(app: App, obj: Bar) -> str:
        return "bar"

    a = App()

    assert a.f(Foo()) == "foo"
    assert a.f(Bar()) == "bar"
    assert a.f(Other()) == "fallback"


def test_dispatch_external_predicates_predicate_fallback() -> None:
    class App(morepath.App):
        @morepath.dispatch_method()
        def f(app, obj: Any) -> str:
            return "dispatch function"

    class Foo:
        pass

    class Bar:
        pass

    class Other:
        pass

    @App.predicate(App.f, name="model", default=None, index=ClassIndex)
    def f_obj(app: App, obj: object) -> type[Any]:
        return obj.__class__

    @App.predicate_fallback(App.f, f_obj)
    def f_obj_fallback(app: App, obj: Any) -> str:
        return "f_obj_fallback"

    @App.method(App.f, model=Foo)
    def f_foo(app: App, obj: Foo) -> str:
        return "foo"

    @App.method(App.f, model=Bar)
    def f_bar(app: App, obj: Foo) -> str:
        return "bar"

    a = App()

    assert a.f(Foo()) == "foo"
    assert a.f(Bar()) == "bar"
    assert a.f(Other()) == "f_obj_fallback"


def test_dispatch_external_predicates_ordering_after() -> None:
    class App(morepath.App):
        @morepath.dispatch_method()
        def f(app, obj: Any, name: str) -> str:
            return "fallback"

    class Foo:
        pass

    class Bar:
        pass

    class Other:
        pass

    @App.predicate(App.f, name="model", default=None, index=ClassIndex)
    def pred_obj(app: App, obj: object, name: str) -> type[Any]:
        return obj.__class__

    @App.predicate(
        App.f, name="name", default="", index=KeyIndex, after=pred_obj
    )
    def pred_name(app: App, obj: object, name: str) -> str:
        return name

    @App.method(App.f, model=Foo, name="")
    def f_foo_default(app: App, obj: Foo, name: str) -> str:
        return "foo default"

    @App.method(App.f, model=Foo, name="edit")
    def f_foo_edit(app: App, obj: Foo, name: str) -> str:
        return "foo edit"

    @App.method(App.f, model=Bar, name="")
    def f_bar_default(app: App, obj: Bar, name: str) -> str:
        return "bar default"

    @App.method(App.f, model=Bar, name="edit")
    def f_bar_edit(app: App, obj: Bar, name: str) -> str:
        return "bar edit"

    a = App()

    assert a.f(Foo(), "") == "foo default"
    assert a.f(Bar(), "") == "bar default"
    assert a.f(Foo(), "edit") == "foo edit"
    assert a.f(Bar(), "edit") == "bar edit"

    assert a.f(Other(), "") == "fallback"
    assert a.f(Other(), "edit") == "fallback"


def test_dispatch_external_predicates_ordering_before() -> None:
    class App(morepath.App):
        @morepath.dispatch_method()
        def f(app, obj: Any, name: str) -> str:
            return "fallback"

    class Foo:
        pass

    class Bar:
        pass

    class Other:
        pass

    @App.predicate(App.f, name="name", default="", index=KeyIndex)
    def pred_name(app: App, obj: object, name: str) -> str:
        return name

    @App.predicate(
        App.f, name="model", default=None, index=ClassIndex, before=pred_name
    )
    def pred_obj(app: App, obj: object, name: str) -> type[Any]:
        return obj.__class__

    @App.method(App.f, model=Foo, name="")
    def f_foo_default(app: App, obj: Foo, name: str) -> str:
        return "foo default"

    @App.method(App.f, model=Foo, name="edit")
    def f_foo_edit(app: App, obj: Foo, name: str) -> str:
        return "foo edit"

    @App.method(App.f, model=Bar, name="")
    def f_bar_default(app: App, obj: Bar, name: str) -> str:
        return "bar default"

    @App.method(App.f, model=Bar, name="edit")
    def f_bar_edit(app: App, obj: Bar, name: str) -> str:
        return "bar edit"

    a = App()

    assert a.f(Foo(), "") == "foo default"
    assert a.f(Bar(), "") == "bar default"
    assert a.f(Foo(), "edit") == "foo edit"
    assert a.f(Bar(), "edit") == "bar edit"

    assert a.f(Other(), "") == "fallback"
    assert a.f(Other(), "edit") == "fallback"


def test_dispatch_external_override_fallback() -> None:
    class App(morepath.App):
        @morepath.dispatch_method()
        def f(self, obj: Any) -> str:
            return "dispatch function"

    class Sub(App):
        pass

    class Foo:
        pass

    class Bar:
        pass

    class Other:
        pass

    @App.predicate(App.f, name="model", default=None, index=ClassIndex)
    def f_obj(self: App, obj: object) -> type[Any]:
        return obj.__class__

    @App.predicate_fallback(App.f, f_obj)
    def f_obj_fallback(self: App, obj: object) -> str:
        return "f_obj_fallback"

    @Sub.predicate_fallback(App.f, f_obj)
    def f_obj_fallback_sub(self: Sub, obj: object) -> str:
        return "f_obj_fallback sub"

    @App.method(App.f, model=Foo)
    def f_foo(self: App, obj: Foo) -> str:
        return "foo"

    @Sub.method(App.f, model=Foo)
    def f_foo_sub(self: Sub, obj: Foo) -> str:
        return "foo sub"

    @App.method(App.f, model=Bar)
    def f_bar(self: App, obj: Bar) -> str:
        return "bar"

    s = Sub()

    assert s.f(Foo()) == "foo sub"
    assert s.f(Bar()) == "bar"
    assert s.f(Other()) == "f_obj_fallback sub"

    # original is unaffected
    a = App()

    assert a.f(Foo()) == "foo"
    assert a.f(Bar()) == "bar"
    assert a.f(Other()) == "f_obj_fallback"


def test_dispatch_external_override_predicate() -> None:
    class App(morepath.App):
        @morepath.dispatch_method()
        def f(app, obj: Any) -> str:
            return "dispatch function"

    class Sub(App):
        pass

    class Foo:
        pass

    class Bar:
        pass

    class Other:
        pass

    @App.predicate(App.f, name="model", default=None, index=ClassIndex)
    def f_obj(app: App, obj: object) -> type[Any]:
        return obj.__class__

    @Sub.predicate(App.f, name="model", default=None, index=ClassIndex)
    def f_obj_sub(app: Sub, obj: object) -> type[Bar]:
        return Bar  # ridiculous, but lets us test this

    @App.predicate_fallback(App.f, f_obj)
    def f_obj_fallback(app: App, obj: object) -> str:
        return "f_obj_fallback"

    @App.method(App.f, model=Foo)
    def f_foo(app: App, obj: Foo) -> str:
        return "foo"

    @Sub.method(App.f, model=Foo)
    def f_foo_sub(app: Sub, obj: Foo) -> str:
        return "foo"

    @App.method(App.f, model=Bar)
    def f_bar(app: App, obj: Bar) -> str:
        return "bar"

    @Sub.method(App.f, model=Bar)
    def f_bar_sub(app: Sub, obj: Bar) -> str:
        return "bar sub"

    s = Sub()

    assert s.f(Foo()) == "bar sub"
    assert s.f(Bar()) == "bar sub"
    assert s.f(Other()) == "bar sub"

    a = App()

    assert a.f(Foo()) == "foo"
    assert a.f(Bar()) == "bar"
    assert a.f(Other()) == "f_obj_fallback"


def test_wrong_predicate_arguments_single() -> None:
    class App(morepath.App):
        @morepath.dispatch_method("obj")
        def f(self, obj: Any) -> str:
            return "fallback"

    class Foo:
        pass

    @App.method(App.f, wrong=Foo)
    def f_foo(app: App, obj: object) -> str:
        return "foo"

    a = App()

    assert a.f(Foo()) == "fallback"


def test_wrong_predicate_arguments_multi() -> None:
    class App(morepath.App):
        @morepath.dispatch_method("a", "b")
        def f(self, a: Any, b: Any) -> str:
            return "fallback"

    class Foo:
        pass

    @App.method(App.f, wrong=Foo)
    def f_foo(app: App, a: object, b: object) -> str:
        return "foo"

    a = App()

    assert a.f(Foo(), Foo()) == "fallback"


def test_dispatch_external_predicates_without_predicate_directives() -> None:
    class App(morepath.App):
        @morepath.dispatch_method()
        def f(self, obj: Any) -> str:
            return "fallback"

    class Foo:
        pass

    class Bar:
        pass

    class Other:
        pass

    @App.method(App.f)
    def f_foo(app: App, obj: object) -> str:
        return "foo"

    a = App()

    assert a.f(Foo()) == "foo"
