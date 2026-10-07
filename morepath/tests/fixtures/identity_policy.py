import morepath


class App(morepath.App):
    pass


class Model:
    def __init__(self, id: str) -> None:
        self.id = id


class Permission:
    pass


@App.path(model=Model, path="{id}")
def get_model(id: str) -> Model:
    return Model(id)


@App.view(model=Model, permission=Permission)
def default(self: Model, request: morepath.Request) -> str:
    return f"Model: {self.id}"


@App.permission_rule(model=Model, permission=Permission)
def model_permission(
    identity: morepath.Identity, model: Model, permission: Permission
) -> bool:
    return model.id == "foo"


class IdentityPolicy:
    def identify(
        self, request: morepath.Request
    ) -> morepath.Identity | morepath.authentication.NoIdentity | None:
        return morepath.Identity("testidentity")

    def remember(
        self,
        response: morepath.Response,
        request: morepath.Request,
        identity: morepath.Identity,
    ) -> None:
        pass

    def forget(
        self,
        response: morepath.Response,
        request: morepath.Request,
        identity: morepath.Identity,
    ) -> None:
        pass


@App.identity_policy()
def get_identity_policy() -> IdentityPolicy:
    return IdentityPolicy()


@App.verify_identity()
def verify_identity(identity: morepath.Identity) -> bool:
    return True
