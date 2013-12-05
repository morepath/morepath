import morepath
from morepath import setup
from morepath.app import global_app
from morepath.request import Response
from werkzeug.test import Client


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

    def get_permission(request, model, permission):
        if model.id == 'foo':
            return True
        else:
            return False

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
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'Model: foo'
    response = c.get('/bar')
    assert response.status == '401 UNAUTHORIZED'
