from morepath.app import App
from morepath import setup
from morepath.request import Response
from werkzeug.test import Client


def test_view_predicates():
    config = setup()
    app = App(testing_config=config)

    @app.root()
    class Root(object):
        pass

    @app.view(model=Root, name='foo', request_method='GET')
    def get(request, model):
        return 'GET'

    @app.view(model=Root, name='foo', request_method='POST')
    def post(request, model):
        return 'POST'

    config.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'GET'
    response = c.post('/foo')
    assert response.data == 'POST'


def test_extra_predicates():
    config = setup()
    app = App(testing_config=config)

    @app.model(path='{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.view(model=Model, name='foo', id='a')
    def get_a(request, model):
        return 'a'

    @app.view(model=Model, name='foo', id='b')
    def get_b(request, model):
        return 'b'

    @app.predicate(name='id', order=2, default='')
    def get_id(request, model):
        return model.id
    config.commit()

    c = Client(app, Response)

    response = c.get('/a/foo')
    assert response.data == 'a'
    response = c.post('/b/foo')
    assert response.data == 'b'
