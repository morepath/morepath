import morepath


class App(morepath.App):
    pass


class Model:
    def __init__(self, id):
        self.id = id


class Permission:
    pass


@App.path(model=Model, path="{id}")
def get_model(id):
    return Model(id)


@App.view(model=Model, permission=Permission)
def default(self, request):
    return "Model: %s" % self.id


@App.permission_rule(model=Model, permission=Permission)
def model_permission(identity, model, permission):
    return model.id == "foo"


class IdentityPolicy:
    def identify(self, request):
        return morepath.Identity("testidentity")

    def remember(self, response, request, identity):
        return []

    def forget(self, response, request):
        return []


@App.identity_policy()
def get_identity_policy():
    return IdentityPolicy()


@App.verify_identity()
def verify_identity(identity):
    return True
