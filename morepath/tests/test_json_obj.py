import morepath
from webtest import TestApp as Client


def test_json_obj_dump():
    class app(morepath.App):
        pass

    @app.path(path='/models/{x}')
    class Model(object):
        def __init__(self, x):
            self.x = x

    @app.json(model=Model)
    def default(self, request):
        return self

    @app.dump_json(model=Model)
    def dump_model_json(self, request):
        return {'x': self.x}

    c = Client(app())

    response = c.get('/models/foo')
    assert response.json == {'x': 'foo'}


def test_json_obj_dump_app_arg():
    class App(morepath.App):
        pass

    @App.path(path='/models/{x}')
    class Model(object):
        def __init__(self, x):
            self.x = x

    @App.json(model=Model)
    def default(self, request):
        return self

    @App.dump_json(model=Model)
    def dump_model_json(app, obj, request):
        assert isinstance(app, App)
        return {'x': obj.x}

    c = Client(App())

    response = c.get('/models/foo')
    assert response.json == {'x': 'foo'}
