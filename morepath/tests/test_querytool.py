from __future__ import annotations

from typing import TYPE_CHECKING, Any

import dectate
import morepath
import reg
from morepath import core

from .fixtures import identity_policy

if TYPE_CHECKING:
    from collections.abc import Iterable


def objects(actions: Iterable[tuple[dectate.Action, Any]]) -> list[Any]:
    result = []
    for action, obj in actions:
        result.append(obj)
    return result


def test_setting() -> None:
    class App(morepath.App):
        pass

    @App.setting(section="foo", name="bar")
    def f() -> str:
        return "Hello"

    @App.setting(section="foo", name="qux")
    def g() -> str:
        return "Dag"

    dectate.commit(App)

    assert objects(dectate.query_app(App, "setting")) == [f, g]

    assert objects(dectate.query_app(App, "setting", name="bar")) == [f]

    assert objects(dectate.query_app(App, "setting_section")) == [f, g]


def test_predicate_fallback() -> None:
    class App(morepath.App):
        pass

    dectate.commit(App)

    r = objects(dectate.query_app(App, "predicate_fallback"))
    assert r == [
        core.model_not_found,
        core.name_not_found,
        core.method_not_allowed,
    ]

    r = objects(
        dectate.query_app(
            App, "predicate_fallback", dispatch="morepath.App.get_view"
        )
    )
    assert r == [
        core.model_not_found,
        core.name_not_found,
        core.method_not_allowed,
    ]

    # there aren't any predicates for class_path
    r = objects(
        dectate.query_app(
            App, "predicate_fallback", dispatch="morepath.App._class_path"
        )
    )
    assert r == []

    r = objects(
        dectate.query_app(
            App, "predicate_fallback", func="morepath.core.model_predicate"
        )
    )
    assert r == [
        core.model_not_found,
    ]


def test_predicate() -> None:
    class App(morepath.App):
        pass

    dectate.commit(App)

    r = objects(dectate.query_app(App, "predicate"))
    assert r == [
        core.model_predicate,
        core.name_predicate,
        core.request_method_predicate,
    ]

    r = objects(
        dectate.query_app(App, "predicate", dispatch="morepath.App.get_view")
    )
    assert r == [
        core.model_predicate,
        core.name_predicate,
        core.request_method_predicate,
    ]

    # there aren't any predicates for class_path
    r = objects(
        dectate.query_app(App, "predicate", dispatch="morepath.App._class_path")
    )
    assert r == []

    r = objects(dectate.query_app(App, "predicate", name="name"))
    assert r == [
        core.name_predicate,
    ]

    r = objects(dectate.query_app(App, "predicate", index="reg.ClassIndex"))
    assert r == [core.model_predicate]

    r = objects(
        dectate.query_app(
            App, "predicate", after="morepath.core.model_predicate"
        )
    )
    assert r == [core.name_predicate]


class App(morepath.App):
    @morepath.dispatch_method()
    def generic(self, v: str) -> str | None:
        pass


def test_method() -> None:
    @App.predicate(App.generic, name="v", default="", index=reg.KeyIndex)
    def get(self: App, v: str) -> str:
        return v

    @App.method(App.generic, v="A")
    def a(app: App, v: str) -> str:
        return v

    @App.method(App.generic, v="B")
    def b(app: App, v: str) -> str:
        return v

    dectate.commit(App)

    app = App()

    assert app.generic("A") == "A"
    assert app.generic("B") == "B"

    r = objects(dectate.query_app(App, "method"))
    assert r == [a, b]

    r = objects(
        dectate.query_app(
            App,
            "method",
            dispatch_method="morepath.tests.test_querytool.App.generic",
        )
    )
    assert r == [a, b]

    r = objects(dectate.query_app(App, "method", v="A"))
    assert r == [a]


def test_converter() -> None:
    class App(morepath.App):
        pass

    dectate.commit(App)

    r = objects(dectate.query_app(App, "converter"))

    expected = [core.int_converter, core.unicode_converter]

    expected.extend([core.date_converter, core.datetime_converter])

    assert r == expected

    r = objects(dectate.query_app(App, "converter", type="builtins.int"))

    assert r == [core.int_converter]


class Foos:
    pass


class Base:
    pass


class Foo(Base):
    pass


class SubFoo(Foo):
    pass


class Bar(Base):
    pass


class SubBar(Bar):
    pass


def get_variables(obj: Any) -> dict[str, Any]:
    return {}


def get_converters() -> dict[str, Any]:
    return {}


def test_path() -> None:
    class App(morepath.App):
        pass

    @App.path("base", model=Base)
    def get_base() -> None:
        pass

    @App.path("foos", model=Foos, variables=get_variables)
    def get_foos() -> None:
        pass

    @App.path(
        "foos/{id}", model=Foo, get_converters=get_converters, absorb=True
    )
    def get_foo(id: str) -> None:
        pass

    dectate.commit(App)

    r = objects(dectate.query_app(App, "path"))

    assert r == [get_base, get_foos, get_foo]

    r = objects(
        dectate.query_app(
            App, "path", model="morepath.tests.test_querytool.Foo"
        )
    )
    assert r == [get_base, get_foo]

    r = objects(
        dectate.query_app(
            App, "path", model="morepath.tests.test_querytool.SubFoo"
        )
    )

    assert r == [get_base, get_foo]

    r = objects(
        dectate.query_app(
            App, "path", model="morepath.tests.test_querytool.Base"
        )
    )

    assert r == [get_base]

    r = objects(
        dectate.query_app(
            App, "path", model="morepath.tests.test_querytool.Bar"
        )
    )

    assert r == [get_base]

    r = objects(dectate.query_app(App, "path", path="foos"))

    assert r == [get_foos]

    r = objects(dectate.query_app(App, "path", path="/foos"))

    assert r == [get_foos]

    r = objects(dectate.query_app(App, "path", path="foos/{id}"))

    assert r == [get_foo]

    r = objects(dectate.query_app(App, "path", path="foos/{blah}"))

    assert r == [get_foo]

    r = objects(
        dectate.query_app(
            App, "path", variables="morepath.tests.test_querytool.get_variables"
        )
    )

    assert r == [get_foos]

    r = objects(
        dectate.query_app(
            App,
            "path",
            get_converters="morepath.tests.test_querytool.get_converters",
        )
    )

    assert r == [get_foo]

    r = objects(dectate.query_app(App, "path", absorb="True"))

    assert r == [get_foo]


class BasePermission:
    pass


class Permission(BasePermission):
    pass


class SubPermission(Permission):
    pass


class SubIdentity(morepath.Identity):
    pass


def test_permission_rule() -> None:
    class App(morepath.App):
        pass

    @App.permission_rule(model=Base, permission=BasePermission)
    def rule_base(obj: Base, permission: object, identity: object) -> bool:
        return True

    @App.permission_rule(model=Foo, permission=Permission)
    def rule_foo(obj: Foo, permission: object, identity: object) -> bool:
        return True

    @App.permission_rule(
        model=Foos, permission=SubPermission, identity=SubIdentity
    )
    def rule_foos(obj: Foos, permission: object, identity: object) -> bool:
        return True

    dectate.commit(App)

    r = objects(dectate.query_app(App, "permission_rule"))

    assert r == [rule_base, rule_foo, rule_foos]

    r = objects(
        dectate.query_app(
            App, "permission_rule", model="morepath.tests.test_querytool.Foo"
        )
    )

    assert r == [rule_base, rule_foo]

    r = objects(
        dectate.query_app(
            App, "permission_rule", model="morepath.tests.test_querytool.Base"
        )
    )

    assert r == [rule_base]

    r = objects(
        dectate.query_app(
            App, "permission_rule", model="morepath.tests.test_querytool.Bar"
        )
    )

    assert r == [rule_base]

    r = objects(
        dectate.query_app(
            App,
            "permission_rule",
            permission="morepath.tests.test_querytool.Permission",
        )
    )

    assert r == [rule_foo, rule_foos]

    r = objects(
        dectate.query_app(
            App,
            "permission_rule",
            permission="morepath.tests.test_querytool.BasePermission",
        )
    )

    assert r == [rule_base, rule_foo, rule_foos]

    r = objects(
        dectate.query_app(
            App,
            "permission_rule",
            permission="morepath.tests.test_querytool.SubPermission",
        )
    )

    assert r == [rule_foos]

    r = objects(
        dectate.query_app(
            App,
            "permission_rule",
            model="morepath.tests.test_querytool.Foo",
            permission="morepath.tests.test_querytool.BasePermission",
        )
    )

    assert r == [rule_base, rule_foo]

    r = objects(
        dectate.query_app(App, "permission_rule", identity="morepath.Identity")
    )

    assert r == [rule_base, rule_foo, rule_foos]

    r = objects(
        dectate.query_app(
            App,
            "permission_rule",
            identity="morepath.tests.test_querytool.SubIdentity",
        )
    )

    assert r == [rule_foos]


def template_directory_a() -> str:
    return "/"


def test_template_directory() -> None:
    class App(morepath.App):
        pass

    # non-decorator so we can import template_directory_a
    App.template_directory()(template_directory_a)

    @App.template_directory(after=template_directory_a, name="blah")
    def b() -> str:
        return "/"

    dectate.commit(App)

    r = objects(dectate.query_app(App, "template_directory"))

    assert r == [template_directory_a, b]

    r = objects(dectate.query_app(App, "template_directory", name="blah"))

    assert r == [b]

    r = objects(
        dectate.query_app(
            App,
            "template_directory",
            after="morepath.tests.test_querytool.template_directory_a",
        )
    )
    assert r == [b]


def test_template_render() -> None:
    class App(morepath.App):
        pass

    @App.template_render(".zpt")
    def render(loader: object, name: str, original_render: object) -> None:
        pass

    @App.template_render(".blah")
    def render2(loader: object, name: str, original_render: object) -> None:
        pass

    dectate.commit(App)

    r = objects(dectate.query_app(App, "template_render"))

    assert r == [render, render2]

    r = objects(dectate.query_app(App, "template_render", extension=".blah"))

    assert r == [render2]


def test_view() -> None:
    class App(morepath.App):
        pass

    @App.json(model=Foo)
    def foo_default(self: Foo, request: morepath.Request) -> None:
        pass

    @App.view(model=Base)
    def base_default(self: Base, request: morepath.Request) -> None:
        pass

    @App.view(model=Foo, name="edit")
    def foo_edit(self: Foo, request: morepath.Request) -> None:
        pass

    dectate.commit(App)

    r = objects(dectate.query_app(App, "view"))

    assert r == [
        core.standard_exception_view,
        foo_default,
        base_default,
        foo_edit,
    ]

    r = objects(dectate.query_app(App, "json"))

    assert r == [
        core.standard_exception_view,
        foo_default,
        base_default,
        foo_edit,
    ]

    r = objects(
        dectate.query_app(
            App, "view", model="morepath.tests.test_querytool.Base"
        )
    )

    assert r == [base_default]

    r = objects(
        dectate.query_app(
            App, "view", model="morepath.tests.test_querytool.Foo"
        )
    )

    assert r == [foo_default, base_default, foo_edit]

    r = objects(
        dectate.query_app(
            App, "view", model="morepath.tests.test_querytool.Bar"
        )
    )

    assert r == [base_default]

    r = objects(dectate.query_app(App, "view", name="edit"))

    assert r == [foo_edit]


def test_view_permission() -> None:
    class App(morepath.App):
        pass

    @App.view(model=Foo, name="n")
    def foo_n(self: Foo, request: morepath.Request) -> None:
        pass

    @App.view(model=Foo, name="b", permission=BasePermission)
    def foo_b(self: Foo, request: morepath.Request) -> None:
        pass

    @App.view(model=Foo, name="p", permission=Permission)
    def foo_p(self: Foo, request: morepath.Request) -> None:
        pass

    @App.view(model=Foo, name="s", permission=SubPermission)
    def foo_s(self: Foo, request: morepath.Request) -> None:
        pass

    dectate.commit(App)

    r = objects(
        dectate.query_app(
            App,
            "view",
            permission="morepath.tests.test_querytool.BasePermission",
        )
    )

    assert r == [foo_b, foo_p, foo_s]

    r = objects(
        dectate.query_app(
            App, "view", permission="morepath.tests.test_querytool.Permission"
        )
    )

    assert r == [foo_p, foo_s]

    r = objects(
        dectate.query_app(
            App,
            "view",
            permission="morepath.tests.test_querytool.SubPermission",
        )
    )

    assert r == [foo_s]

    r = objects(
        dectate.query_app(
            App,
            "view",
            model="morepath.tests.test_querytool.Foo",
            permission="builtins.None",
        )
    )

    assert r == [foo_n]


class Mounted(morepath.App):
    pass


def test_mount() -> None:
    class App(morepath.App):
        pass

    @App.path(path="foo", model=Foo)
    def get_foo() -> None:
        pass

    @App.mount(path="mounted", app=Mounted)
    def mount_app() -> Mounted:
        return Mounted()

    dectate.commit(App, Mounted)

    r = objects(dectate.query_app(App, "mount"))

    assert r == [get_foo, mount_app]

    r = objects(
        dectate.query_app(
            App, "mount", app="morepath.tests.test_querytool.Mounted"
        )
    )

    assert r == [mount_app]

    r = objects(
        dectate.query_app(
            App, "mount", model="morepath.tests.test_querytool.Foo"
        )
    )

    assert r == [get_foo]


def test_defer_links() -> None:
    class App(morepath.App):
        pass

    class Mounted2(morepath.App):
        pass

    @App.path(path="foo", model=Foo)
    def get_foo() -> None:
        pass

    @App.defer_links(model=Bar)
    def defer_bar(app: App, obj: Bar) -> morepath.App | None:
        return app.child("mounted")

    @App.mount(path="mounted", app=Mounted2)
    def mount_app() -> Mounted2:
        return Mounted2()

    dectate.commit(App, Mounted2)

    r = objects(dectate.query_app(App, "defer_links"))

    assert r == [get_foo, defer_bar, mount_app]

    r = objects(
        dectate.query_app(
            App, "defer_links", model="morepath.tests.test_querytool.Bar"
        )
    )

    assert r == [defer_bar]

    r = objects(
        dectate.query_app(
            App, "defer_links", model="morepath.tests.test_querytool.SubBar"
        )
    )

    assert r == [defer_bar]

    r = objects(
        dectate.query_app(
            App, "defer_links", model="morepath.tests.test_querytool.Foo"
        )
    )
    assert r == [get_foo]


if TYPE_CHECKING:
    tween_a_factory: Any
    tween_b_factory: Any
else:

    def tween_a_factory():
        pass

    def tween_b_factory():
        pass


def test_tween_factory() -> None:
    class App(morepath.App):
        pass

    App.tween_factory()(tween_a_factory)
    App.tween_factory(over=tween_a_factory)(tween_b_factory)

    dectate.commit(App)

    r = objects(dectate.query_app(App, "tween_factory"))

    assert r == [
        core.excview_tween_factory,
        core.poisoned_host_header_protection_tween_factory,
        tween_a_factory,
        tween_b_factory,
    ]

    r = objects(
        dectate.query_app(
            App,
            "tween_factory",
            over="morepath.tests.test_querytool.tween_a_factory",
        )
    )

    assert r == [tween_b_factory]


def test_identity_policy() -> None:
    class App(morepath.App):
        pass

    @App.identity_policy()
    def get_identity_policy() -> identity_policy.IdentityPolicy:
        return identity_policy.IdentityPolicy()

    dectate.commit(App)

    r = objects(dectate.query_app(App, "identity_policy"))

    assert len(r) == 1


def test_verify_identity() -> None:
    class App(morepath.App):
        pass

    @App.verify_identity()
    def verify(identity: morepath.Identity) -> bool:
        return True

    dectate.commit(App)

    r = objects(dectate.query_app(App, "verify_identity"))

    assert r == [verify]


def test_dump_json() -> None:
    class App(morepath.App):
        pass

    @App.dump_json(model=Foo)
    def dump_foo(self: Foo, request: morepath.Request) -> None:
        pass

    @App.dump_json(model=Bar)
    def dump_bar(self: Bar, request: morepath.Request) -> None:
        pass

    dectate.commit(App)

    r = objects(dectate.query_app(App, "dump_json"))

    assert r == [dump_foo, dump_bar]

    r = objects(
        dectate.query_app(
            App, "dump_json", model="morepath.tests.test_querytool.Foo"
        )
    )

    assert r == [dump_foo]

    r = objects(
        dectate.query_app(
            App, "dump_json", model="morepath.tests.test_querytool.SubFoo"
        )
    )

    assert r == [dump_foo]


def test_link_prefix() -> None:
    class App(morepath.App):
        pass

    @App.link_prefix()
    def prefix(s: App) -> None:
        pass

    dectate.commit(App)

    r = objects(dectate.query_app(App, "link_prefix"))

    assert r == [prefix]
