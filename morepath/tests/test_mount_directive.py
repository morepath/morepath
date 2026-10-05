from __future__ import annotations

from typing import Any

import pytest
from webtest import TestApp as Client

import morepath
from morepath.error import ConflictError, LinkError


def test_model_mount_conflict() -> None:
    class App(morepath.App):
        pass

    class App2(morepath.App):
        pass

    class A:
        pass

    @App.path(model=A, path="a")
    def get_a() -> A:
        return A()

    @App.mount(app=App2, path="a")
    def get_mount() -> App2:
        return App2()

    with pytest.raises(ConflictError):
        App.commit()


def test_mount_basic() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, id: str) -> None:
            self.id = id

    @Mounted.path(path="")
    class MountedRoot:
        pass

    @Mounted.view(model=MountedRoot)
    def root_default(self: MountedRoot, request: morepath.Request) -> str:
        return "The root"

    @Mounted.view(model=MountedRoot, name="link")
    def root_link(self: MountedRoot, request: morepath.Request) -> str:
        return request.link(self)

    @App.mount(path="{id}", app=Mounted)
    def get_mounted(id: str) -> Mounted:
        return Mounted(id=id)

    c = Client(App())

    response = c.get("/foo")
    assert response.body == b"The root"

    response = c.get("/foo/link")
    assert response.body == b"http://localhost/foo"


def test_mounted_app_classes() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, id: str) -> None:
            self.id = id

    class Sub(morepath.App):
        pass

    @App.mount(path="{id}", app=Mounted)
    def get_mounted(id: str) -> Mounted:
        return Mounted(id=id)

    @Mounted.mount(path="sub", app=Sub)
    def get_sub() -> Sub:
        return Sub()

    assert App.commit() == {App, Mounted, Sub}

    assert App.mounted_app_classes() == {App, Mounted, Sub}


def test_mounted_app_classes_nothing_mounted() -> None:
    class App(morepath.App):
        pass

    assert App.commit() == {App}

    assert App.mounted_app_classes() == {App}


def test_mount_none_should_fail() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        pass

    @Mounted.path(path="")
    class MountedRoot:
        pass

    @Mounted.view(model=MountedRoot)
    def root_default(self: MountedRoot, request: morepath.Request) -> str:
        return "The root"

    @Mounted.view(model=MountedRoot, name="link")
    def root_link(self: MountedRoot, request: morepath.Request) -> str:
        return request.link(self)

    @App.mount(path="{id}", app=Mounted)
    def mount_mounted(id: str) -> None:
        return None

    c = Client(App())

    c.get("/foo", status=404)
    c.get("/foo/link", status=404)


def test_mount_context() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, mount_id: str) -> None:
            self.mount_id = mount_id

    @Mounted.path(path="")
    class MountedRoot:
        def __init__(self, app: Mounted) -> None:
            self.mount_id = app.mount_id

    @Mounted.view(model=MountedRoot)
    def root_default(self: MountedRoot, request: morepath.Request) -> str:
        return "The root for mount id: %s" % self.mount_id

    @App.mount(path="{id}", app=Mounted)
    def get_context(id: str) -> Mounted:
        return Mounted(mount_id=id)

    c = Client(App())

    response = c.get("/foo")
    assert response.body == b"The root for mount id: foo"
    response = c.get("/bar")
    assert response.body == b"The root for mount id: bar"


def test_mount_context_parameters() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, mount_id: int) -> None:
            self.mount_id = mount_id

    @Mounted.path(path="")
    class MountedRoot:
        def __init__(self, app: Mounted) -> None:
            assert isinstance(app.mount_id, int)
            self.mount_id = app.mount_id

    @Mounted.view(model=MountedRoot)
    def root_default(self: MountedRoot, request: morepath.Request) -> str:
        return "The root for mount id: %s" % self.mount_id

    @App.mount(path="mounts", app=Mounted)
    def get_context(mount_id: int = 0) -> Mounted:
        return Mounted(mount_id=mount_id)

    c = Client(App())

    response = c.get("/mounts?mount_id=1")
    assert response.body == b"The root for mount id: 1"
    response = c.get("/mounts")
    assert response.body == b"The root for mount id: 0"


def test_mount_context_parameters_override_default() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, mount_id: str) -> None:
            self.mount_id = mount_id

    @Mounted.path(path="")
    class MountedRoot:
        def __init__(self, app: Mounted, mount_id: str) -> None:
            self.mount_id = mount_id
            self.app_mount_id = app.mount_id

    @Mounted.view(model=MountedRoot)
    def root_default(self: MountedRoot, request: morepath.Request) -> str:
        return "mount_id: {} app_mount_id: {}".format(
            self.mount_id,
            self.app_mount_id,
        )

    @App.mount(path="{id}", app=Mounted)
    def get_context(id: str) -> Mounted:
        return Mounted(mount_id=id)

    c = Client(App())

    response = c.get("/foo")
    assert response.body == b"mount_id: None app_mount_id: foo"
    # the URL parameter mount_id cannot interfere with the mounting
    # process
    response = c.get("/bar?mount_id=blah")
    assert response.body == b"mount_id: blah app_mount_id: bar"


def test_mount_context_standalone() -> None:
    class App(morepath.App):
        def __init__(self, mount_id: str) -> None:
            self.mount_id = mount_id

    @App.path(path="")
    class Root:
        def __init__(self, app: App) -> None:
            self.mount_id = app.mount_id

    @App.view(model=Root)
    def root_default(self: Root, request: morepath.Request) -> str:
        return "The root for mount id: %s" % self.mount_id

    c = Client(App(mount_id="foo"))

    response = c.get("/")
    assert response.body == b"The root for mount id: foo"


def test_mount_parent_link() -> None:
    class App(morepath.App):
        pass

    @App.path(path="models/{id}")
    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    class Mounted(morepath.App):
        def __init__(self, mount_id: str) -> None:
            self.mount_id = mount_id

    @Mounted.path(path="")
    class MountedRoot:
        def __init__(self, mount_id: str) -> None:
            self.mount_id = mount_id

    @Mounted.view(model=MountedRoot)
    def root_default(self: MountedRoot, request: morepath.Request) -> str:
        assert request.app.parent is not None
        return request.link(Model("one"), app=request.app.parent)

    @App.mount(path="{id}", app=Mounted)
    def get_context(id: str) -> Mounted:
        return Mounted(mount_id=id)

    c = Client(App())

    response = c.get("/foo")
    assert response.body == b"http://localhost/models/one"


def test_mount_child_link() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, mount_id: str) -> None:
            self.mount_id = mount_id

    @Mounted.path(path="models/{id}")
    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @App.path(path="")
    class Root:
        pass

    @App.view(model=Root)
    def app_root_default(self: Root, request: morepath.Request) -> str:
        child = request.app.child(Mounted, id="foo")
        assert child is not None
        return request.link(Model("one"), app=child)

    @App.view(model=Root, name="inst")
    def app_root_inst(self: Root, request: morepath.Request) -> str:
        child = request.app.child(Mounted(mount_id="foo"))
        assert child is not None
        return request.link(Model("one"), app=child)

    @App.mount(path="{id}", app=Mounted, variables=lambda a: {"id": a.mount_id})
    def get_context(id: str) -> Mounted:
        return Mounted(mount_id=id)

    c = Client(App())

    response = c.get("/")
    assert response.body == b"http://localhost/foo/models/one"
    response = c.get("/+inst")
    assert response.body == b"http://localhost/foo/models/one"


def test_mount_sibling_link() -> None:
    class App(morepath.App):
        pass

    class first(morepath.App):
        pass

    class second(morepath.App):
        pass

    @first.path(path="models/{id}")
    class FirstModel:
        def __init__(self, id: str) -> None:
            self.id = id

    @first.view(model=FirstModel)
    def first_model_default(self: FirstModel, request: morepath.Request) -> str:
        sibling = request.app.sibling("second")
        assert sibling is not None
        return request.link(SecondModel(2), app=sibling)

    @second.path(path="foos/{id}")
    class SecondModel:
        def __init__(self, id: int) -> None:
            self.id = id

    @App.path(path="")
    class Root:
        pass

    @App.mount(path="first", app=first)
    def get_context_first() -> first:
        return first()

    @App.mount(path="second", app=second)
    def get_context_second() -> second:
        return second()

    c = Client(App())

    response = c.get("/first/models/1")
    assert response.body == b"http://localhost/second/foos/2"


def test_mount_sibling_link_at_root_app() -> None:
    class App(morepath.App):
        pass

    @App.path(path="")
    class Root:
        pass

    class Item:
        def __init__(self, id: int) -> None:
            self.id = id

    @App.view(model=Root)
    def root_default(self: Root, request: morepath.Request) -> str:
        return request.link(Item(3), app=request.app.sibling("foo"))  # type: ignore

    c = Client(App())

    with pytest.raises(LinkError):
        c.get("/")


def test_mount_child_link_unknown_child() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, mount_id: str) -> None:
            self.mount_id = mount_id

    @Mounted.path(path="models/{id}")
    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @App.path(path="")
    class Root:
        pass

    @App.view(model=Root)
    def app_root_default(self: Root, request: morepath.Request) -> str:
        child = request.app.child(Mounted, id="foo")
        if child is None:
            return "link error"
        return request.link(Model("one"), app=child)

    @App.view(model=Root, name="inst")
    def app_root_inst(self: Root, request: morepath.Request) -> str:
        child = request.app.child(Mounted(mount_id="foo"))
        if child is None:
            return "link error"
        return request.link(Model("one"), app=child)

    # no mount directive so linking will fail

    c = Client(App())

    response = c.get("/")
    assert response.body == b"link error"
    response = c.get("/+inst")
    assert response.body == b"link error"


def test_mount_child_link_unknown_parent() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @App.path(path="")
    class Root:
        pass

    @App.view(model=Root)
    def app_root_default(self: Root, request: morepath.Request) -> str:
        parent = request.app.parent
        if parent is None:
            return "link error"
        return request.link(Model("one"), app=parent)

    c = Client(App())

    response = c.get("/")
    assert response.body == b"link error"


def test_mount_child_link_unknown_app() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, mount_id: str) -> None:
            self.mount_id = mount_id

    @Mounted.path(path="models/{id}")
    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @App.path(path="")
    class Root:
        pass

    @App.view(model=Root)
    def app_root_default(self: Root, request: morepath.Request) -> str:
        child = request.app.child(Mounted, id="foo")
        try:
            return request.link(Model("one"), app=child)  # type: ignore
        except LinkError:
            return "link error"

    # no mounting, so Mounted is unknown when making link

    c = Client(App())

    response = c.get("/")
    assert response.body == b"link error"


def test_mount_link_prefix() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, mount_id: str) -> None:
            self.mount_id = mount_id

    @App.mount(path="/mnt/{id}", app=Mounted, variables=lambda a: dict(id=a.mount_id))
    def get_mounted(id: str) -> Mounted:
        return Mounted(mount_id=id)

    @App.path(path="")
    class AppRoot:
        pass

    @Mounted.path(path="")
    class MountedRoot:
        pass

    @App.link_prefix()
    def link_prefix(request: morepath.Request) -> str:
        return "http://app"

    @Mounted.link_prefix()
    def mounted_link_prefix(request: morepath.Request) -> str:
        return "http://mounted"

    @App.view(model=AppRoot, name="get-root-link")
    def get_root_link(self: AppRoot, request: morepath.Request) -> str:
        return request.link(self)

    @Mounted.view(model=MountedRoot, name="get-mounted-root-link")
    def get_mounted_root_link(self: MountedRoot, request: morepath.Request) -> str:
        return request.link(self)

    @Mounted.view(model=MountedRoot, name="get-root-link-through-mount")
    def get_root_link_through_mount(
        self: MountedRoot, request: morepath.Request
    ) -> Any:
        parent = request.app.parent
        assert parent is not None
        return request.view(AppRoot(), app=parent, name="get-root-link")

    c = Client(App())

    # response = c.get('/get-root-link')
    # assert response.body == b'http://app/'

    # response = c.get('/mnt/1/get-mounted-root-link')
    # assert response.body == b'http://mounted/mnt/1'

    response = c.get("/mnt/1/get-root-link-through-mount")
    assert response.body == b"http://app/"

    response = c.get("/get-root-link")
    assert response.body == b"http://app/"


def test_request_view_in_mount() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, mount_id: str) -> None:
            self.mount_id = mount_id

    @App.path(path="")
    class Root:
        pass

    @Mounted.path(path="models/{id}")
    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @Mounted.view(model=Model)
    def model_default(self: Model, request: morepath.Request) -> dict[str, str]:
        return {"hey": "Hey"}

    @App.view(model=Root)
    def root_default(self: Root, request: morepath.Request) -> Any:
        child = request.app.child(Mounted, id="foo")
        assert child is not None
        result = request.view(Model("x"), app=child)
        assert result is not None
        return result["hey"]

    @App.view(model=Root, name="inst")
    def root_inst(self: Root, request: morepath.Request) -> Any:
        child = request.app.child(Mounted(mount_id="foo"))
        assert child is not None
        result = request.view(Model("x"), app=child)
        assert result is not None
        return result["hey"]

    @App.mount(path="{id}", app=Mounted, variables=lambda a: dict(id=a.mount_id))
    def get_context(id: str) -> Mounted:
        return Mounted(mount_id=id)

    c = Client(App())

    response = c.get("/")
    assert response.body == b"Hey"

    response = c.get("/+inst")
    assert response.body == b"Hey"


def test_request_link_child_child() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, mount_id: str) -> None:
            self.mount_id = mount_id

    class submounted(morepath.App):
        pass

    @App.path(path="")
    class Root:
        pass

    @App.view(model=Root)
    def root_default(self: Root, request: morepath.Request) -> Any:
        child: morepath.App | None = request.app.child(Mounted, id="foo")
        assert child is not None
        child = child.child(submounted)
        assert child is not None
        return request.view(SubRoot(), app=child)

    @App.view(model=Root, name="inst")
    def root_inst(self: Root, request: morepath.Request) -> Any:
        child: morepath.App | None = request.app.child(Mounted(mount_id="foo"))
        assert child is not None
        child = child.child(submounted())
        assert child is not None
        return request.view(SubRoot(), app=child)

    @App.view(model=Root, name="info")
    def root_info(self: Root, request: morepath.Request) -> str:
        return "info"

    @App.mount(path="{id}", app=Mounted, variables=lambda a: dict(mount_id=a.mount_id))
    def get_context(id: str) -> Mounted:
        return Mounted(mount_id=id)

    @Mounted.mount(path="sub", app=submounted)
    def get_context2() -> submounted:
        return submounted()

    @submounted.path(path="")
    class SubRoot:
        pass

    @submounted.view(model=SubRoot)
    def subroot_default(self: SubRoot, request: morepath.Request) -> str:
        return "SubRoot"

    @submounted.view(model=SubRoot, name="parentage")
    def subroot_parentage(self: SubRoot, request: morepath.Request) -> Any:
        parent = request.app.parent
        assert parent is not None
        ancestor = parent.parent
        assert ancestor is not None
        return request.view(Root(), name="info", app=ancestor)

    c = Client(App())

    response = c.get("/")
    assert response.body == b"SubRoot"
    response = c.get("/+inst")
    assert response.body == b"SubRoot"

    response = c.get("/foo/sub/parentage")
    assert response.body == b"info"


def test_request_view_in_mount_broken() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, mount_id: str) -> None:
            self.mount_id = mount_id

    @App.path(path="")
    class Root:
        pass

    @Mounted.path(path="models/{id}")
    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @Mounted.view(model=Model)
    def model_default(self: Model, request: morepath.Request) -> dict[str, str]:
        return {"hey": "Hey"}

    @App.view(model=Root)
    def root_default(self: Root, request: morepath.Request) -> Any:
        child = request.app.child(Mounted, id="foo")
        try:
            return request.view(Model("x"), app=child)["hey"]  # type: ignore
        except LinkError:
            return "link error"

    @App.view(model=Root, name="inst")
    def root_inst(self: Root, request: morepath.Request) -> Any:
        child = request.app.child(Mounted(mount_id="foo"))
        try:
            return request.view(Model("x"), app=child)["hey"]  # type: ignore
        except LinkError:
            return "link error"

    @App.view(model=Root, name="doublechild")
    def doublechild(self: Root, request: morepath.Request) -> str | None:
        try:
            request.app.child(Mounted, id="foo").child(Mounted, id="bar")  # type: ignore
        except AttributeError:
            return "link error"
        else:
            return None

    @App.view(model=Root, name="childparent")
    def childparent(self: Root, request: morepath.Request) -> str | None:
        try:
            request.app.child(Mounted, id="foo").parent  # type: ignore
        except AttributeError:
            return "link error"
        else:
            return None

    # deliberately don't mount so using view is broken

    c = Client(App())

    response = c.get("/")
    assert response.body == b"link error"

    response = c.get("/+inst")
    assert response.body == b"link error"

    response = c.get("/doublechild")
    assert response.body == b"link error"

    response = c.get("/childparent")
    assert response.body == b"link error"


def test_mount_implicit_converters() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, id: int) -> None:
            self.id = id

    class MountedRoot:
        def __init__(self, id: int) -> None:
            self.id = id

    @Mounted.path(path="", model=MountedRoot)
    def get_root(app: Mounted) -> MountedRoot:
        return MountedRoot(app.id)

    @Mounted.view(model=MountedRoot)
    def root_default(self: MountedRoot, request: morepath.Request) -> str:
        return f"The root for: {self.id} {type(self.id)}"

    @App.mount(path="{id}", app=Mounted)
    def get_context(id: int = 0) -> Mounted:
        return Mounted(id=id)

    c = Client(App())

    response = c.get("/1")
    assert response.body in (
        b"The root for: 1 <type 'int'>",
        b"The root for: 1 <class 'int'>",
    )


def test_mount_explicit_converters() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, id: int) -> None:
            self.id = id

    class MountedRoot:
        def __init__(self, id: int) -> None:
            self.id = id

    @Mounted.path(path="", model=MountedRoot)
    def get_root(app: Mounted) -> MountedRoot:
        return MountedRoot(id=app.id)

    @Mounted.view(model=MountedRoot)
    def root_default(self: MountedRoot, request: morepath.Request) -> str:
        return f"The root for: {self.id} {type(self.id)}"

    @App.mount(path="{id}", app=Mounted, converters=dict(id=int))
    def get_context(id: int) -> Mounted:
        return Mounted(id=id)

    c = Client(App())

    response = c.get("/1")
    assert response.body in (
        b"The root for: 1 <type 'int'>",
        b"The root for: 1 <class 'int'>",
    )


def test_mount_view_in_child_view() -> None:
    class App(morepath.App):
        pass

    class fooapp(morepath.App):
        pass

    @App.path(path="")
    class Root:
        pass

    @App.view(model=Root)
    def default_homepage(self: Root, request: morepath.Request) -> Any:
        child = request.app.child(fooapp)
        assert child is not None
        return request.view(FooRoot(), app=child)

    @fooapp.path(path="")
    class FooRoot:
        pass

    @fooapp.view(model=FooRoot, name="name")
    def foo_name(self: FooRoot, request: morepath.Request) -> str:
        return "Foo"

    @fooapp.view(model=FooRoot)
    def foo_default(self: FooRoot, request: morepath.Request) -> str:
        result = request.view(self, name="name")
        assert isinstance(result, str)
        return "Hello " + result

    @App.mount(path="foo", app=fooapp)
    def mount_to_root() -> fooapp:
        return fooapp()

    c = Client(App())

    response = c.get("/foo")
    assert response.body == b"Hello Foo"

    response = c.get("/")
    assert response.body == b"Hello Foo"


def test_mount_view_in_child_view_then_parent_view() -> None:
    class App(morepath.App):
        pass

    class fooapp(morepath.App):
        pass

    @App.path(path="")
    class Root:
        pass

    @App.view(model=Root)
    def default_homepage(self: Root, request: morepath.Request) -> str:
        other = request.app.child(fooapp)
        assert other is not None
        return "{} {}".format(
            request.view(FooRoot(), app=other),
            request.view(self, name="other"),
        )

    @App.view(model=Root, name="other")
    def root_other(self: Root, request: morepath.Request) -> str:
        return "other"

    @fooapp.path(path="")
    class FooRoot:
        pass

    @fooapp.view(model=FooRoot, name="name")
    def foo_name(self: FooRoot, request: morepath.Request) -> str:
        return "Foo"

    @fooapp.view(model=FooRoot)
    def foo_default(self: FooRoot, request: morepath.Request) -> str:
        return "Hello {}".format(request.view(self, name="name"))

    @App.mount(path="foo", app=fooapp)
    def mount_to_root() -> fooapp:
        return fooapp()

    c = Client(App())

    response = c.get("/")
    assert response.body == b"Hello Foo other"


def test_mount_directive_with_link_and_absorb() -> None:
    class App1(morepath.App):
        pass

    @App1.path(path="")
    class Model1:
        pass

    class App2(morepath.App):
        pass

    class Model2:
        def __init__(self, absorb: str) -> None:
            self.absorb = absorb

    @App2.path(model=Model2, path="", absorb=True)
    def get_model(absorb: str) -> Model2:
        return Model2(absorb)

    @App2.view(model=Model2)
    def default(self: Model2, request: morepath.Request) -> str:
        return f"A:{self.absorb} L:{request.link(self)}"

    @App1.mount(path="foo", app=App2)
    def get_mount() -> App2:
        return App2()

    c = Client(App1())

    response = c.get("/foo")
    assert response.body == b"A: L:http://localhost/foo"

    response = c.get("/foo/bla")
    assert response.body == b"A:bla L:http://localhost/foo/bla"


def test_mount_named_child_link_explicit_name() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        pass

    @Mounted.path(path="models/{id}")
    class Model:
        def __init__(self, id: str):
            self.id = id

    @App.path(path="")
    class Root:
        pass

    @App.view(model=Root)
    def app_root_default(self: Root, request: morepath.Request) -> str:
        child = request.app.child(Mounted)
        assert child is not None
        return request.link(Model("one"), app=child)

    @App.view(model=Root, name="extra")
    def app_root_default2(self: Root, request: morepath.Request) -> str:
        child = request.app.child("sub")
        assert child is not None
        return request.link(Model("one"), app=child)

    @App.mount(path="subapp", app=Mounted, name="sub")
    def get_context() -> Mounted:
        return Mounted()

    c = Client(App())

    response = c.get("/")
    assert response.body == b"http://localhost/subapp/models/one"

    response = c.get("/extra")
    assert response.body == b"http://localhost/subapp/models/one"


def test_mount_named_child_link_name_defaults_to_path() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        pass

    @Mounted.path(path="models/{id}")
    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @App.path(path="")
    class Root:
        pass

    @App.view(model=Root)
    def app_root_default(self: Root, request: morepath.Request) -> str:
        child = request.app.child(Mounted)
        assert child is not None
        return request.link(Model("one"), app=child)

    @App.view(model=Root, name="extra")
    def app_root_default2(self: Root, request: morepath.Request) -> str:
        child = request.app.child("subapp")
        assert child is not None
        return request.link(Model("one"), app=child)

    @App.mount(path="subapp", app=Mounted)
    def get_context() -> Mounted:
        return Mounted()

    c = Client(App())

    response = c.get("/")
    assert response.body == b"http://localhost/subapp/models/one"

    response = c.get("/extra")
    assert response.body == b"http://localhost/subapp/models/one"


def test_named_mount_with_parameters() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, mount_id: int) -> None:
            self.mount_id = mount_id

    @App.path(path="")
    class Root:
        pass

    @Mounted.path(path="")
    class MountedRoot:
        def __init__(self, mount_id: int) -> None:
            assert isinstance(mount_id, int)
            self.mount_id = mount_id

    @Mounted.view(model=MountedRoot)
    def root_default(self: MountedRoot, request: morepath.Request) -> str:
        return "The root for mount id: %s" % self.mount_id

    @App.mount(path="mounts/{mount_id}", app=Mounted)
    def get_context(mount_id: int = 0) -> Mounted:
        return Mounted(mount_id=mount_id)

    class Item:
        def __init__(self, id: str | int) -> None:
            self.id = id

    @Mounted.path(path="items/{id}", model=Item)
    def get_item(id: str) -> Item:
        return Item(id)

    @App.view(model=Root)
    def root_default2(self: Root, request: morepath.Request) -> str:
        child = request.app.child("mounts/{mount_id}", mount_id=3)
        assert child is not None
        return request.link(Item(4), app=child)

    c = Client(App())

    response = c.get("/")
    assert response.body == b"http://localhost/mounts/3/items/4"


def test_named_mount_with_url_parameters() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, mount_id: int) -> None:
            self.mount_id = mount_id

    @App.path(path="")
    class Root:
        pass

    @Mounted.path(path="")
    class MountedRoot:
        def __init__(self, mount_id: int) -> None:
            assert isinstance(mount_id, int)
            self.mount_id = mount_id

    @Mounted.view(model=MountedRoot)
    def root_default(self: MountedRoot, request: morepath.Request) -> str:
        return "The root for mount id: %s" % self.mount_id

    @App.mount(path="mounts", app=Mounted)
    def get_context(mount_id: int = 0) -> Mounted:
        return Mounted(mount_id=mount_id)

    class Item:
        def __init__(self, id: str | int) -> None:
            self.id = id

    @Mounted.path(path="items/{id}", model=Item)
    def get_item(id: str) -> Item:
        return Item(id)

    @App.view(model=Root)
    def root_default2(self: Root, request: morepath.Request) -> str:
        child = request.app.child("mounts", mount_id=3)
        assert child is not None
        return request.link(Item(4), app=child)

    c = Client(App())

    response = c.get("/")
    assert response.body == b"http://localhost/mounts/items/4?mount_id=3"


def test_access_app_through_request() -> None:
    class root(morepath.App):
        pass

    class sub(morepath.App):
        def __init__(self, name: str) -> None:
            self.name = name

    @root.path(path="")
    class RootModel:
        pass

    @root.view(model=RootModel)
    def root_model_default(self: RootModel, request: morepath.Request) -> str:
        child = request.app.child(sub, mount_name="foo")
        assert child is not None
        return request.link(SubModel("foo"), app=child)

    class SubModel:
        def __init__(self, name: str) -> None:
            self.name = name

    @sub.path(path="", model=SubModel)
    def get_sub_model(request: morepath.Request[sub]) -> SubModel:
        return SubModel(request.app.name)

    @root.mount(
        app=sub, path="{mount_name}", variables=lambda a: {"mount_name": a.name}
    )
    def mount_sub(mount_name: str) -> sub:
        return sub(name=mount_name)

    c = Client(root())

    response = c.get("/")
    assert response.body == b"http://localhost/foo"


def test_mount_ancestors() -> None:
    class App(morepath.App):
        pass

    class Mounted(morepath.App):
        def __init__(self, id: str) -> None:
            self.id = id

    @App.path(path="")
    class AppRoot:
        pass

    @App.view(model=AppRoot)
    def app_root_default(self: AppRoot, request: morepath.Request) -> None:
        ancestors = list(request.app.ancestors())
        assert len(ancestors) == 1
        assert ancestors[0] is request.app
        assert request.app.root is request.app

    @Mounted.path(path="")
    class MountedRoot:
        pass

    @Mounted.view(model=MountedRoot)
    def mounted_root_default(self: MountedRoot, request: morepath.Request) -> None:
        ancestors = list(request.app.ancestors())
        assert len(ancestors) == 2
        assert ancestors[0] is request.app
        assert ancestors[1] is request.app.parent
        assert request.app.root is request.app.parent

    @App.mount(path="{id}", app=Mounted)
    def get_mounted(id: str) -> Mounted:
        return Mounted(id=id)

    c = Client(App())

    c.get("/")
    c.get("/foo")


def test_breadthfist_vs_inheritance_on_commit() -> None:
    class Root(morepath.App):
        pass

    class App1(morepath.App):
        pass

    class ExtendedApp1(App1):
        pass

    class App2(morepath.App):
        pass

    class ExtendedApp2(App2):
        pass

    @App1.path(path="")
    class Model1:
        pass

    @App2.path(path="")
    class Model2:
        pass

    @App1.view(model=Model1)
    def view1(self: Model1, request: morepath.Request) -> str:
        return type(request.app).__name__

    @App2.view(model=Model2)
    def view2(self: Model2, request: morepath.Request) -> str:
        return type(request.app).__name__

    Root.mount(app=App1, path="a/")(App1)
    App1.mount(app=App2, path="b/")(App2)

    Root.mount(app=ExtendedApp2, path="x/")(ExtendedApp2)
    ExtendedApp2.mount(app=ExtendedApp1, path="y/")(ExtendedApp1)

    # NB: ExtendedApp2 is mounted higher app in the tree than App2,
    # from which it inherits.  This means that ExtendedApp2 is
    # discovered before App2.  The purpose of this test is to ensure
    # that this potentially problematic situation is in fact harmless,
    # i.e., that the breadth-first order in which apps are discovered,
    # which is not in general a valid traversal of the inheritance
    # graph, does not lead to partial commits and hence to
    # misconfigurations.

    c = Client(Root())

    response = c.get("/a")
    assert response.body == b"App1"

    response = c.get("/a/b")
    assert response.body == b"App2"

    response = c.get("/x")
    assert response.body == b"ExtendedApp2"

    response = c.get("/x/y")
    assert response.body == b"ExtendedApp1"
