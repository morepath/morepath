import morepath


class app(morepath.App):
    pass


class Model(object):
    def __init__(self, id):
        self.id = id


class Permission(object):
    pass


@app.path(model=Model, path='{id}')
def get_model(id):
    return Model(id)


@app.view(model=Model, permission=Permission)
def default(self, request):
    return "Model: %s" % self.id


@app.permission_rule(model=Model, permission=Permission)
def model_permission(identity, model, permission):
    return model.id == 'foo'


class IdentityPolicy(object):
    def identify(self, request):
        return morepath.Identity('testidentity')

    def remember(self, response, request, identity):
        return []

    def forget(self, response, request):
        return []


@app.identity_policy()
def get_identity_policy():
    return IdentityPolicy()


@app.verify_identity()
def verify_identity(identity):
    return True
