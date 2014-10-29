import morepath
from webtest import TestApp as Client


def setup_module(module):
    morepath.disable_implicit()


def test_json_obj_dump():
    config = morepath.setup()

    class app(morepath.App):
        testing_config = config

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

    config.commit()

    c = Client(app())

    response = c.get('/models/foo')
    assert response.json == {'x': 'foo'}


def test_json_obj_load():
    config = morepath.setup()

    class app(morepath.App):
        testing_config = config

    class Collection(object):
        def __init__(self):
            self.items = []

        def add(self, item):
            self.items.append(item)

    collection = Collection()

    @app.path(path='/', model=Collection)
    def get_collection():
        return collection

    @app.json(model=Collection, request_method='POST')
    def default(self, request):
        self.add(request.body_obj)
        return 'done'

    class Item(object):
        def __init__(self, value):
            self.value = value

    @app.load_json()
    def load_json(json, request):
        return Item(json['x'])

    config.commit()

    c = Client(app())

    c.post_json('/', {'x': 'foo'})

    assert len(collection.items) == 1
    assert isinstance(collection.items[0], Item)
    assert collection.items[0].value == 'foo'
