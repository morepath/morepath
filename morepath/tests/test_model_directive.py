import morepath
from morepath import setup
from morepath.request import Response
from morepath.converter import Converter

from werkzeug.test import Client
import pytest


def test_simple_path_one_step():
    app = morepath.App()

    class Model(object):
        def __init__(self):
            pass

    def get_model():
        return Model()

    def default(request, model):
        return "View"

    def link(request, model):
        return request.link(model)

    c = setup()
    c.configurable(app)
    c.action(app.model(model=Model, path='simple'), get_model)
    c.action(app.view(model=Model), default)
    c.action(app.view(model=Model, name='link'), link)
    c.commit()

    c = Client(app, Response)

    response = c.get('/simple')
    assert response.data == 'View'

    response = c.get('/simple/link')
    assert response.data == '/simple'


def test_simple_path_two_steps():
    app = morepath.App()

    class Model(object):
        def __init__(self):
            pass

    def get_model():
        return Model()

    def default(request, model):
        return "View"

    def link(request, model):
        return request.link(model)

    c = setup()
    c.configurable(app)
    c.action(app.model(model=Model, path='one/two'), get_model)
    c.action(app.view(model=Model), default)
    c.action(app.view(model=Model, name='link'), link)
    c.commit()

    c = Client(app, Response)

    response = c.get('/one/two')
    assert response.data == 'View'

    response = c.get('/one/two/link')
    assert response.data == '/one/two'


def test_variable_path_one_step():
    app = morepath.App()

    class Model(object):
        def __init__(self, name):
            self.name = name

    def get_model(name):
        return Model(name)

    def default(request, model):
        return "View: %s" % model.name

    def link(request, model):
        return request.link(model)

    c = setup()
    c.configurable(app)
    c.action(app.model(model=Model, path='{name}'), get_model)
    c.action(app.view(model=Model), default)
    c.action(app.view(model=Model, name='link'), link)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'View: foo'

    response = c.get('/foo/link')
    assert response.data == '/foo'


def test_variable_path_two_steps():
    app = morepath.App()

    class Model(object):
        def __init__(self, name):
            self.name = name

    def get_model(name):
        return Model(name)

    def default(request, model):
        return "View: %s" % model.name

    def link(request, model):
        return request.link(model)

    c = setup()
    c.configurable(app)
    c.action(app.model(model=Model, path='document/{name}'), get_model)
    c.action(app.view(model=Model), default)
    c.action(app.view(model=Model, name='link'), link)
    c.commit()

    c = Client(app, Response)

    response = c.get('/document/foo')
    assert response.data == 'View: foo'

    response = c.get('/document/foo/link')
    assert response.data == '/document/foo'


def test_variable_path_two_variables():
    app = morepath.App()

    class Model(object):
        def __init__(self, name, version):
            self.name = name
            self.version = version

    def get_model(name, version):
        return Model(name, version)

    def default(request, model):
        return "View: %s %s" % (model.name, model.version)

    def link(request, model):
        return request.link(model)

    c = setup()
    c.configurable(app)
    c.action(app.model(model=Model, path='{name}-{version}'),
             get_model)
    c.action(app.view(model=Model), default)
    c.action(app.view(model=Model, name='link'), link)
    c.commit()

    c = Client(app, Response)

    response = c.get('foo-one')
    assert response.data == 'View: foo one'

    response = c.get('/foo-one/link')
    assert response.data == '/foo-one'


def test_variable_path_explicit_type():
    app = morepath.App()

    class Model(object):
        def __init__(self, id):
            self.id = id

    def get_model(id):
        return Model(id)

    def default(request, model):
        return "View: %s (%s)" % (model.id, type(model.id))

    def link(request, model):
        return request.link(model)

    c = setup()
    c.configurable(app)
    c.action(app.model(model=Model, path='{id}',
                       converters=dict(id=Converter(int))),
             get_model)
    c.action(app.view(model=Model), default)
    c.action(app.view(model=Model, name='link'), link)
    c.commit()

    c = Client(app, Response)

    response = c.get('1')
    assert response.data == "View: 1 (<type 'int'>)"

    response = c.get('/1/link')
    assert response.data == '/1'

    response = c.get('broken')
    assert response.status == '404 NOT FOUND'
