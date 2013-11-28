from morepath.app import App
from morepath.config import Config
from morepath import setup
from morepath.request import Response
from werkzeug.test import Client


def test_view_predicates():
    setup()

    app = App()

    class Root(object):
        pass

    def get(request, model):
        return 'GET'

    def post(request, model):
        return 'POST'

    c = Config()
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
