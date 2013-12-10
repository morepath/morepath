import morepath
from morepath import setup
from morepath.request import Response
from werkzeug.test import Client
from morepath.security import Identity, BasicAuthIdentityPolicy
from .fixtures import identity_policy
import pytest


def test_no_permission():
    app = morepath.App()

    class Model(object):
        def __init__(self, id):
            self.id = id

    def get_model(id):
        return Model(id)

    def default(request, model):
        return "Model: %s" % model.id

    class Permission(object):
        pass

    c = setup()
    c.configurable(app)
    c.action(app.model(model=Model, path='{id}',
                       variables=lambda model: {'id': model.id}),
             get_model)
    c.action(app.view(model=Model, permission=Permission),
             default)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.status == '401 UNAUTHORIZED'


def test_permission_directive():
    app = morepath.App()

    class Model(object):
        def __init__(self, id):
            self.id = id

    def get_model(id):
        return Model(id)

    def get_permission(identity, model, permission):
        if model.id == 'foo':
            return True
        else:
            return False

    def default(request, model):
        return "Model: %s" % model.id

    class Permission(object):
        pass

    class IdentityPolicy(object):
        def identity(self, request):
            return Identity('testidentity')

        def remember(self, request, identity):
            return []

        def forget(self, request):
            return []

    c = setup()
    c.configurable(app)
    c.action(app.model(model=Model, path='{id}',
                       variables=lambda model: {'id': model.id}),
             get_model)
    c.action(app.permission(model=Model, permission=Permission),
             get_permission)
    c.action(app.view(model=Model, permission=Permission),
             default)
    c.action(app.identity_policy(), IdentityPolicy)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'Model: foo'
    response = c.get('/bar')
    assert response.status == '401 UNAUTHORIZED'


def test_policy_action():
    config = setup()
    config.scan(identity_policy)
    config.commit()

    c = Client(identity_policy.app, Response)

    response = c.get('/foo')
    assert response.data == 'Model: foo'
    response = c.get('/bar')
    assert response.status == '401 UNAUTHORIZED'


@pytest.mark.xfail()
def test_basic_auth_identity_policy():
    app = morepath.App()

    class Model(object):
        def __init__(self, id):
            self.id = id

    def get_model(id):
        return Model(id)

    def get_permission(identity, model, permission):
        return identity.userid == 'one'

    def default(request, model):
        return "Model: %s" % model.id

    class Permission(object):
        pass

    c = setup()
    c.configurable(app)
    c.action(app.model(model=Model, path='{id}',
                       variables=lambda model: {'id': model.id}),
             get_model)
    c.action(app.permission(model=Model, permission=Permission),
             get_permission)
    c.action(app.view(model=Model, permission=Permission),
             default)
    c.action(app.identity_policy(), BasicAuthIdentityPolicy)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.status == '401 UNAUTHORIZED'

    # XXX need a way to construct auth headers here
    response = c.get('/foo')
    assert response.data == 'Model: foo'
