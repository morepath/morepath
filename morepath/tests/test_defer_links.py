from __future__ import annotations

from typing import Any

import pytest
from webtest import TestApp as Client

import morepath
from morepath.error import ConflictError, LinkError


def test_defer_links() -> None:
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path="")
    class RootModel:
        pass

    @Root.view(model=RootModel)
    def root_model_default(self: RootModel, request: morepath.Request) -> str:
        return request.link(SubModel())

    @Root.view(model=RootModel, name="class_link")
    def root_model_class_link(self: RootModel, request: morepath.Request) -> str:
        return request.class_link(SubModel)

    @Sub.path(path="")
    class SubModel:
        pass

    @Root.mount(app=Sub, path="sub")
    def mount_sub() -> Sub:
        return Sub()

    @Root.defer_links(model=SubModel)
    def defer_links_sub_model(app: Root, obj: SubModel) -> morepath.App | None:
        return app.child(Sub())

    c = Client(Root())

    response = c.get("/")
    assert response.body == b"http://localhost/sub"

    with pytest.raises(LinkError):
        c.get("/class_link")


def test_defer_view() -> None:
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path="")
    class RootModel:
        pass

    @Root.json(model=RootModel)
    def root_model_default(self: RootModel, request: morepath.Request) -> Any:
        return request.view(SubModel())

    @Sub.path(path="")
    class SubModel:
        pass

    @Sub.json(model=SubModel)
    def submodel_default(self: SubModel, request: morepath.Request) -> dict[str, Any]:
        return {"hello": "world"}

    @Root.mount(app=Sub, path="sub")
    def mount_sub() -> Sub:
        return Sub()

    @Root.defer_links(model=SubModel)
    def defer_links_sub_model(app: Root, obj: SubModel) -> morepath.App | None:
        return app.child(Sub())

    c = Client(Root())

    response = c.get("/")
    assert response.json == {"hello": "world"}


def test_defer_view_predicates() -> None:
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path="")
    class RootModel:
        pass

    @Root.json(model=RootModel)
    def root_model_default(self: RootModel, request: morepath.Request) -> Any:
        return request.view(SubModel(), name="edit")

    @Sub.path(path="")
    class SubModel:
        pass

    @Sub.json(model=SubModel, name="edit")
    def submodel_edit(self: Sub, request: SubModel) -> dict[str, Any]:
        return {"hello": "world"}

    @Root.mount(app=Sub, path="sub")
    def mount_sub() -> Sub:
        return Sub()

    @Root.defer_links(model=SubModel)
    def defer_links_sub_model(app: Root, obj: SubModel) -> morepath.App | None:
        return app.child(Sub())

    c = Client(Root())

    response = c.get("/")
    assert response.json == {"hello": "world"}


def test_defer_view_missing_view() -> None:
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path="")
    class RootModel:
        pass

    @Root.json(model=RootModel)
    def root_model_default(
        self: RootModel, request: morepath.Request
    ) -> dict[str, Any]:
        return {"not_found": request.view(SubModel(), name="unknown")}

    @Sub.path(path="")
    class SubModel:
        pass

    @Sub.json(model=SubModel, name="edit")
    def submodel_edit(self: Sub, request: morepath.Request) -> dict[str, Any]:
        return {"hello": "world"}

    @Root.mount(app=Sub, path="sub")
    def mount_sub() -> Sub:
        return Sub()

    @Root.defer_links(model=SubModel)
    def defer_links_sub_model(app: Root, obj: SubModel) -> morepath.App | None:
        return app.child(Sub())

    c = Client(Root())

    response = c.get("/")
    assert response.json == {"not_found": None}


def test_defer_links_mount_parameters() -> None:
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        def __init__(self, name: str) -> None:
            self.name = name

    @Root.path(path="")
    class RootModel:
        pass

    class SubModel:
        def __init__(self, name: str) -> None:
            self.name = name

    @Root.view(model=RootModel)
    def root_model_default(self: RootModel, request: morepath.Request) -> str:
        return request.link(SubModel("foo"))

    @Sub.path(path="", model=SubModel)
    def get_sub_model(request: morepath.Request[Sub]) -> SubModel:
        return SubModel(request.app.name)

    @Root.mount(
        app=Sub, path="{mount_name}", variables=lambda a: {"mount_name": a.name}
    )
    def mount_sub(mount_name: str) -> Sub:
        return Sub(name=mount_name)

    @Root.defer_links(model=SubModel)
    def defer_links_sub_model(app: Root, obj: SubModel) -> morepath.App | None:
        return app.child(Sub(name=obj.name))

    c = Client(Root())

    response = c.get("/")
    assert response.body == b"http://localhost/foo"


def test_defer_link_acquisition() -> None:
    class Root(morepath.App):
        pass

    class Sub(morepath.App):  # pyright: ignore[reportUnusedClass]
        pass

    @Root.path(path="model/{id}")
    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @Root.view(model=Model)
    def model_default(self: Model, request: morepath.Request) -> str:
        return "Hello"

    @Sub.path(path="")
    class SubModel:
        pass

    @Sub.view(model=SubModel)
    def sub_model_default(self: SubModel, request: morepath.Request) -> str:
        return request.link(Model("foo"))

    @Root.mount(app=Sub, path="sub")
    def mount_sub(obj: object, app: Root) -> morepath.App | None:
        return app.child(Sub())

    @Sub.defer_links(model=Model)
    def get_parent(app: Sub, obj: object) -> morepath.App | None:
        return app.parent

    c = Client(Root())

    response = c.get("/sub")
    assert response.body == b"http://localhost/model/foo"


def test_defer_view_acquisition() -> None:
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path="model/{id}")
    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @Root.json(model=Model)
    def model_default(self: Model, request: morepath.Request) -> dict[str, Any]:
        return {"Hello": "World"}

    @Sub.path(path="")
    class SubModel:
        pass

    @Sub.json(model=SubModel)
    def sub_model_default(self: SubModel, request: morepath.Request) -> Any:
        return request.view(Model("foo"))

    @Root.mount(app=Sub, path="sub")
    def mount_sub(obj: object, app: Root) -> morepath.App | None:
        return app.child(Sub())

    @Sub.defer_links(model=Model)
    def get_parent(app: Sub, obj: object) -> morepath.App | None:
        return app.parent

    c = Client(Root())

    response = c.get("/sub")
    assert response.json == {"Hello": "World"}


def test_defer_link_acquisition_blocking() -> None:
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path="model/{id}")
    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @Root.view(model=Model)
    def model_default(self: Model, request: morepath.Request) -> str:
        return "Hello"

    @Sub.path(path="")
    class SubModel:
        pass

    @Sub.view(model=SubModel)
    def sub_model_default(self: SubModel, request: morepath.Request) -> str:
        try:
            return request.link(Model("foo"))
        except LinkError:
            return "link error"

    @Root.mount(app=Sub, path="sub")
    def mount_sub() -> Sub:
        return Sub()

    # no defer_links_to_parent

    c = Client(Root())

    response = c.get("/sub")
    assert response.body == b"link error"


def test_defer_view_acquisition_blocking() -> None:
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path="model/{id}")
    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @Root.json(model=Model)
    def model_default(self: Model, request: morepath.Request) -> dict[str, Any]:
        return {"Hello": "World"}

    @Sub.path(path="")
    class SubModel:
        pass

    @Sub.json(model=SubModel)
    def sub_model_default(self: SubModel, request: morepath.Request) -> bool:
        return request.view(Model("foo")) is None

    @Root.mount(app=Sub, path="sub")
    def mount_sub() -> Sub:
        return Sub()

    # no defer_links_to_parent

    c = Client(Root())

    response = c.get("/sub")
    assert response.json is True


def test_defer_link_should_not_cause_web_views_to_exist() -> None:
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path="")
    class Model:
        pass

    @Root.view(model=Model)
    def model_default(self: Model, request: morepath.Request) -> str:
        return "Hello"

    @Root.view(model=Model, name="extra")
    def model_extra(self: Model, request: morepath.Request) -> str:
        return "Extra"

    # note inheritance from model. we still don't
    # want the extra view to show up on the web
    @Sub.path(path="")
    class SubModel(Model):
        pass

    @Sub.view(model=SubModel)
    def sub_model_default(self: SubModel, request: morepath.Request) -> str:
        return request.link(Model())

    @Root.mount(app=Sub, path="sub")
    def mount_sub() -> Sub:
        return Sub()

    @Sub.defer_links(model=Model)
    def get_parent(app: Sub, obj: Model) -> morepath.App | None:
        return app.parent

    c = Client(Root())

    response = c.get("/sub")
    assert response.body == b"http://localhost/"

    c.get("/sub/+extra", status=404)


def test_defer_link_to_parent_from_root() -> None:
    class Root(morepath.App):
        pass

    @Root.path(path="")
    class Model:
        pass

    class OtherModel:
        pass

    @Root.view(model=Model)
    def model_default(self: Model, request: morepath.Request) -> str:
        return request.link(OtherModel())

    @Root.defer_links(model=OtherModel)
    def get_parent(app: Root, obj: OtherModel) -> morepath.App | None:
        return app.parent

    c = Client(Root())

    with pytest.raises(LinkError):
        c.get("/")


def test_special_link_overrides_deferred_link() -> None:
    class Root(morepath.App):
        pass

    class Alpha(morepath.App):
        pass

    class AlphaModel:
        pass

    class SpecialAlphaModel(AlphaModel):
        pass

    @Root.mount(app=Alpha, path="alpha")
    def mount_alpha() -> Alpha:
        return Alpha()

    @Root.path(path="")
    class RootModel:
        pass

    @Root.path(model=SpecialAlphaModel, path="roots_alpha")
    def get_root_alpha() -> SpecialAlphaModel:
        return SpecialAlphaModel()

    @Root.view(model=RootModel)
    def root_model_default(self: RootModel, request: morepath.Request) -> str:
        return request.link(AlphaModel())

    @Root.view(model=RootModel, name="special")
    def root_model_special(self: RootModel, request: morepath.Request) -> str:
        return request.link(SpecialAlphaModel())

    @Alpha.path(path="", model=AlphaModel)
    def get_alpha() -> AlphaModel:
        return AlphaModel()

    @Root.defer_links(model=AlphaModel)
    def defer_links_alpha(app: Root, obj: AlphaModel) -> morepath.App | None:
        return app.child(Alpha())

    c = Client(Root())

    response = c.get("/")
    assert response.body == b"http://localhost/alpha"

    response = c.get("/special")
    assert response.body == b"http://localhost/roots_alpha"


def test_deferred_deferred_link() -> None:
    class Root(morepath.App):
        pass

    class Alpha(morepath.App):
        pass

    class Beta(morepath.App):
        pass

    @Root.path(path="")
    class RootModel:
        pass

    @Root.view(model=RootModel)
    def root_model_default(self: RootModel, request: morepath.Request) -> str:
        return request.link(AlphaModel())

    @Alpha.path(path="")
    class AlphaModel:
        pass

    @Beta.path(path="")
    class BetaModel:
        pass

    @Beta.view(model=BetaModel)
    def beta_model_default(self: BetaModel, request: morepath.Request) -> str:
        return request.link(AlphaModel())

    @Root.mount(app=Alpha, path="alpha")
    def mount_alpha() -> Alpha:
        return Alpha()

    @Root.mount(app=Beta, path="beta")
    def mount_beta() -> Beta:
        return Beta()

    @Beta.defer_links(model=AlphaModel)
    def defer_links_parent(app: Beta, obj: AlphaModel) -> morepath.App | None:
        return app.parent

    @Root.defer_links(model=AlphaModel)
    def defer_links_alpha(app: Root, obj: AlphaModel) -> morepath.App | None:
        return app.child(Alpha())

    c = Client(Root())

    response = c.get("/")
    assert response.body == b"http://localhost/alpha"

    response = c.get("/beta")
    assert response.body == b"http://localhost/alpha"


def test_deferred_deferred_view() -> None:
    class Root(morepath.App):
        pass

    class Alpha(morepath.App):
        pass

    class Beta(morepath.App):
        pass

    @Root.path(path="")
    class RootModel:
        pass

    @Root.json(model=RootModel)
    def root_model_default(self: RootModel, request: morepath.Request) -> Any:
        return request.view(AlphaModel())

    @Alpha.path(path="")
    class AlphaModel:
        pass

    @Alpha.json(model=AlphaModel)
    def alpha_model_default(
        self: AlphaModel, request: morepath.Request
    ) -> dict[str, Any]:
        return {"model": "alpha"}

    @Beta.path(path="")
    class BetaModel:
        pass

    @Beta.json(model=BetaModel)
    def beta_model_default(self: BetaModel, request: morepath.Request) -> Any:
        return request.view(AlphaModel())

    @Root.mount(app=Alpha, path="alpha")
    def mount_alpha() -> Alpha:
        return Alpha()

    @Root.mount(app=Beta, path="beta")
    def mount_beta() -> Beta:
        return Beta()

    @Beta.defer_links(model=AlphaModel)
    def defer_links_parent(app: Beta, obj: AlphaModel) -> morepath.App | None:
        return app.parent

    @Root.defer_links(model=AlphaModel)
    def defer_links_alpha(app: Root, obj: AlphaModel) -> morepath.App | None:
        return app.child(Alpha())

    c = Client(Root())

    response = c.get("/")
    assert response.json == {"model": "alpha"}

    response = c.get("/beta")
    assert response.json == {"model": "alpha"}


def test_deferred_view_has_app_of_defer() -> None:
    class Root(morepath.App):
        pass

    class Alpha(morepath.App):
        pass

    class Beta(morepath.App):
        pass

    @Root.mount(app=Alpha, path="alpha")
    def mount_alpha() -> Alpha:
        return Alpha()

    @Root.mount(app=Beta, path="beta")
    def mount_beta() -> Beta:
        return Beta()

    @Root.path(path="")
    class RootModel:
        pass

    @Alpha.path(path="")
    class AlphaModel:
        pass

    @Alpha.json(model=AlphaModel)
    def alpha_model_default(self: AlphaModel, request: morepath.Request) -> str:
        if request.app.__class__ == Alpha:
            return "correct"
        else:
            return "wrong"

    @Beta.path(path="")
    class BetaModel:
        pass

    @Beta.json(model=BetaModel)
    def beta_model_default(self: BetaModel, request: morepath.Request) -> Any:
        return request.view(AlphaModel())

    @Beta.defer_links(model=AlphaModel)
    def defer_links_parent(app: Beta, obj: AlphaModel) -> morepath.App | None:
        assert app.parent is not None
        return app.parent.child("alpha")

    c = Client(Root())

    response = c.get("/beta")
    assert response.json == "correct"


def test_deferred_loop() -> None:
    class Root(morepath.App):
        pass

    class Alpha(morepath.App):
        pass

    @Root.path(path="")
    class RootModel:
        pass

    # not actually exposed with path anywhere!
    class Model:
        pass

    @Root.json(model=RootModel)
    def root_model_default(self: RootModel, request: morepath.Request) -> str:
        return request.link(Model())

    @Root.mount(app=Alpha, path="alpha")
    def mount_alpha() -> Alpha:
        return Alpha()

    # setup a loop: defer to parent and back to child!
    @Alpha.defer_links(model=Model)
    def defer_links_parent(app: Alpha, obj: Model) -> morepath.App | None:
        return app.parent

    @Root.defer_links(model=Model)
    def defer_links_alpha(app: Root, obj: Model) -> morepath.App | None:
        return app.child(Alpha())

    c = Client(Root())

    with pytest.raises(LinkError) as ex:
        c.get("/")

    assert "Circular" in str(ex.value)


@pytest.mark.skip(reason="Infinite loop (#479)")
def test_deferred_loop_siblings() -> None:
    # https://github.com/morepath/morepath/issues/479
    class Root(morepath.App):
        pass

    class Alpha(morepath.App):
        pass

    class Beta(morepath.App):
        pass

    @Root.path(path="")
    class RootModel:
        pass

    # not actually exposed with path anywhere!
    class Model:
        pass

    @Root.json(model=RootModel)
    def root_model_default(self: RootModel, request: morepath.Request) -> str:
        return request.link(Model())

    @Root.defer_links(model=Model)
    def defer_links_alpha(app: Root, obj: Model) -> morepath.App | None:
        return app.child(Alpha())

    @Root.mount(app=Alpha, path="alpha")
    def mount_alpha() -> Alpha:
        return Alpha()

    @Root.mount(app=Beta, path="beta")
    def mount_beta() -> Beta:
        return Beta()

    # setup a loop: defer to sibling and back
    @Alpha.defer_links(model=Model)
    def defer_links_to_beta(app: Alpha, obj: Model) -> morepath.App | None:
        return app.sibling(Beta())

    @Beta.defer_links(model=Model)
    def defer_links_to_alpha(app: Beta, obj: Model) -> morepath.App | None:
        return app.sibling(Alpha())

    c = Client(Root())

    with pytest.raises(LinkError) as ex:
        c.get("/")

    assert "Circular" in str(ex.value)


def test_defer_cycle_keys_distinguish_parameterized_mounts() -> None:
    class Root(morepath.App):
        pass

    class Tenant(morepath.App):
        def __init__(self, mount_id: str) -> None:
            self.mount_id = mount_id

    class Model:
        pass

    @Root.mount(
        app=Tenant,
        path="{tenant_id}",
        variables=lambda tenant: {"tenant_id": tenant.mount_id},
    )
    def mount_tenant(tenant_id: str) -> Tenant:
        return Tenant(tenant_id)

    @Root.defer_links(model=Model)
    def defer_to_first_tenant(app: Root, obj: Model) -> morepath.App | None:
        return app.child(Tenant, tenant_id="first")

    @Tenant.defer_links(model=Model)
    def defer_to_next_tenant(app: Tenant, obj: Model) -> morepath.App | None:
        next_tenant = {"first": "second", "second": "third"}.get(app.mount_id)
        if next_tenant is None:
            return None
        return app.sibling(Tenant, tenant_id=next_tenant)

    Root.commit()
    root = Root()

    def find_nothing(app: morepath.App, obj: Model) -> None:
        return None

    # These apps share a class and parent, but their custom mount variables
    # identify distinct locations; the traversal must not report a false loop.
    assert root._follow_defers(find_nothing, Model()) == (None, None)


# see issue #342
def test_defer_link_scenario() -> None:
    class App(morepath.App):
        pass

    class Child(morepath.App):
        pass

    class Document:
        pass

    @App.mount(app=Child, path="child")
    def mount_child() -> Child:
        return Child()

    @App.defer_links(model=Document)
    def defer_document(app: App, doc: Document) -> morepath.App | None:
        return app.child(Child())

    @App.path(path="")
    class Root:
        pass

    @App.json(model=Root)
    def root_view(self: Root, request: morepath.Request) -> dict[str, Any]:
        return {
            "link": request.link(Document()),
            "view": request.view(Document()),
        }

    # if this is commented out, the Child app's view for Document
    # will be used by root_view, which is surprising.
    @App.json(model=Document)
    def app_document_default(
        self: Document, request: morepath.Request
    ) -> dict[str, Any]:
        return {"app": "App"}

    @Child.path("", model=Document)
    def get_document() -> Document:
        return Document()

    @Child.json(model=Document)
    def document_default(self: Document, request: morepath.Request) -> dict[str, Any]:
        return {
            "app": "Child",
        }

    c = Client(App())

    response = c.get("/child")

    assert response.json == {"app": "Child"}

    response = c.get("/")

    # it is rather surprising that the view is not deferred to Child if there
    # is a view defined for App. It is according to spec: the app uses
    # its own behavior if it's there, and only defers afterwards. Is this
    # really what we want, though?
    assert response.json == {
        "link": "http://localhost/child",
        "view": {"app": "App"},
    }


def test_defer_class_links_without_variables() -> None:
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path="")
    class RootModel:
        pass

    @Root.view(model=RootModel)
    def root_model_default(self: RootModel, request: morepath.Request) -> str:
        return request.class_link(SubModel)

    @Sub.path(path="")
    class SubModel:
        pass

    @Root.mount(app=Sub, path="sub")
    def mount_sub() -> Sub:
        return Sub()

    @Root.defer_class_links(model=SubModel, variables=lambda obj: {})
    def defer_class_links_sub_model(
        app: Root, model: SubModel, variables: dict[str, Any]
    ) -> morepath.App | None:
        return app.child(Sub())

    c = Client(Root())

    response = c.get("/")
    assert response.body == b"http://localhost/sub"


def test_defer_class_links_with_variables() -> None:
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path="")
    class RootModel:
        pass

    @Root.view(model=RootModel)
    def root_model_default(self: Root, request: morepath.Request) -> str:
        return request.class_link(SubModel, variables=dict(name="foo"))

    @Sub.path(path="{name}")
    class SubModel:
        def __init__(self, name: str) -> None:
            self.name = name

    @Root.mount(app=Sub, path="sub")
    def mount_sub() -> Sub:
        return Sub()

    @Root.defer_class_links(model=SubModel, variables=lambda obj: {"name": obj.name})
    def defer_class_links_sub_model(
        app: Root, model: SubModel, variables: dict[str, Any]
    ) -> morepath.App | None:
        return app.child(Sub())

    c = Client(Root())

    response = c.get("/")
    assert response.body == b"http://localhost/sub/foo"


def test_deferred_class_link_loop() -> None:
    class Root(morepath.App):
        pass

    class Alpha(morepath.App):
        pass

    @Root.path(path="")
    class RootModel:
        pass

    # not actually exposed with path anywhere!
    class SubModel:
        pass

    @Root.view(model=RootModel)
    def root_model_default(self: RootModel, request: morepath.Request) -> str:
        return request.class_link(SubModel)

    @Root.mount(app=Alpha, path="alpha")
    def mount_alpha() -> Alpha:
        return Alpha()

    # setup a loop: defer to parent and back to child!
    @Alpha.defer_class_links(model=SubModel, variables=lambda obj: {})
    def defer_class_links_parent(
        app: Alpha, obj: SubModel, variables: dict[str, Any]
    ) -> morepath.App | None:
        return app.parent

    @Root.defer_class_links(model=SubModel, variables=lambda obj: {})
    def defer_class_links_alpha(
        app: Root, obj: SubModel, variables: dict[str, Any]
    ) -> morepath.App | None:
        return app.child(Alpha())

    c = Client(Root())

    with pytest.raises(LinkError) as ex:
        c.get("/")

    assert "Circular" in str(ex.value)


def test_link_uses_defer_class_links() -> None:
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path="")
    class RootModel:
        pass

    @Sub.path(path="{name}")
    class SubModel:
        def __init__(self, name: str) -> None:
            self.name = name

    @Root.view(model=RootModel)
    def root_model_default(self: RootModel, request: morepath.Request) -> str:
        return request.link(SubModel("foo"))

    @Root.mount(app=Sub, path="sub")
    def mount_sub() -> Sub:
        return Sub()

    @Root.defer_class_links(model=SubModel, variables=lambda obj: {"name": obj.name})
    def defer_class_links_sub_model(
        app: Root, model: SubModel, variables: dict[str, Any]
    ) -> morepath.App | None:
        return app.child(Sub())

    c = Client(Root())

    response = c.get("/")
    assert response.body == b"http://localhost/sub/foo"


def test_defer_links_and_defer_links_conflict() -> None:
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path="")
    class RootModel:
        pass

    @Sub.path(path="{name}")
    class SubModel:
        def __init__(self, name: str) -> None:
            self.name = name

    @Root.view(model=RootModel)
    def root_model_default(self: RootModel, request: morepath.Request) -> str:
        return request.link(SubModel("foo"))

    @Root.mount(app=Sub, path="sub")
    def mount_sub() -> Sub:
        return Sub()

    @Root.defer_links(model=SubModel)
    def defer_links_sub_model(app: Root, obj: SubModel) -> morepath.App | None:
        return app.child(Sub())

    @Root.defer_class_links(model=SubModel, variables=lambda obj: {"name": obj.name})
    def defer_class_links_sub_model(
        app: Root, model: SubModel, variables: dict[str, Any]
    ) -> morepath.App | None:
        return app.child(Sub())

    with pytest.raises(ConflictError):
        Root.commit()
