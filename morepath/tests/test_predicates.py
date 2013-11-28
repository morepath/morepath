from morepath.app import App, global_app
from morepath.config import Config
from morepath import setup
from morepath.request import Response
from werkzeug.test import Client

def setup_function(function):
    global_app.clear()

def test_view_predicates():
    app = App()

    class Root(object):
        pass

    def get(request, model):
        return 'GET'

    def post(request, model):
        return 'POST'

    c = setup()
    c.configurable(app)
    c.action(app.root(), Root)
    c.action(app.view(model=Root, name='foo', request_method='GET'),
             get)
    c.action(app.view(model=Root, name='foo', request_method='POST'),
             post)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'GET'
    response = c.post('/foo')
    assert response.data == 'POST'
