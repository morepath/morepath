from morepath.app import App

from webtest import TestApp as Client
import morepath
from reg import KeyIndex


def test_view_predicates():
    class app(App):
        pass

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root, name='foo', request_method='GET')
    def get(self, request):
        return 'GET'

    @app.view(model=Root, name='foo', request_method='POST')
    def post(self, request):
        return 'POST'

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'GET'
    response = c.post('/foo')
    assert response.body == b'POST'


def test_extra_predicates():
    class app(App):
        pass

    @app.path(path='{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.view(model=Model, name='foo', id='a')
    def get_a(self, request):
        return 'a'

    @app.view(model=Model, name='foo', id='b')
    def get_b(self, request):
        return 'b'

    @app.predicate(morepath.App.get_view, name='id', default='',
                   index=KeyIndex, after=morepath.request_method_predicate)
    def id_predicate(self, obj, request):
        return obj.id

    c = Client(app())

    response = c.get('/a/foo')
    assert response.body == b'a'
    response = c.get('/b/foo')
    assert response.body == b'b'
