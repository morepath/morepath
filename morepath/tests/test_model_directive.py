import morepath
from morepath import setup
from morepath.request import Response

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
