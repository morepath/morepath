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


def test_json_obj_load():
    class app(morepath.App):
        pass

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

    c = Client(app())

    c.post_json('/', {'x': 'foo'})

    assert len(collection.items) == 1
    assert isinstance(collection.items[0], Item)
    assert collection.items[0].value == 'foo'


def test_json_obj_load_app_arg():
    class App(morepath.App):
        pass

    class Collection(object):
        def __init__(self):
            self.items = []

        def add(self, item):
            self.items.append(item)

    collection = Collection()

    @App.path(path='/', model=Collection)
    def get_collection():
        return collection

    @App.json(model=Collection, request_method='POST')
    def default(self, request):
        self.add(request.body_obj)
        return 'done'

    class Item(object):
        def __init__(self, value):
            self.value = value

    @App.load_json()
    def load_json(app, json, request):
        assert isinstance(app, App)
        return Item(json['x'])

    c = Client(App())

    c.post_json('/', {'x': 'foo'})

    assert len(collection.items) == 1
    assert isinstance(collection.items[0], Item)
    assert collection.items[0].value == 'foo'


def test_json_obj_load_default():
    class app(morepath.App):
        pass

    class Root(object):
        pass

    @app.path(path='/', model=Root)
    def get_root():
        return Root()

    @app.json(model=Root, request_method='POST')
    def default(self, request):
        assert request.body_obj == request.json
        return 'done'

    c = Client(app())

    c.post_json('/', {'x': 'foo'})


def test_json_body_model():
    class app(morepath.App):
        pass

    class Collection(object):
        def __init__(self):
            self.items = []

        def add(self, item):
            self.items.append(item)

    class Item1(object):
        def __init__(self, value):
            self.value = value

    class Item2(object):
        def __init__(self, value):
            self.value = value

    collection = Collection()

    @app.path(path='/', model=Collection)
    def get_collection():
        return collection

    @app.json(model=Collection, request_method='POST',
              body_model=Item1)
    def default(self, request):
        self.add(request.body_obj)
        return 'done'

    @app.load_json()
    def load_json(json, request):
        if json['@type'] == 'Item1':
            return Item1(json['x'])
        elif json['@type'] == 'Item2':
            return Item2(json['x'])

    c = Client(app())

    c.post_json('/', {'@type': 'Item1', 'x': 'foo'})

    assert len(collection.items) == 1
    assert isinstance(collection.items[0], Item1)
    assert collection.items[0].value == 'foo'

    c.post_json('/', {'@type': 'Item2', 'x': 'foo'}, status=422)


def test_json_obj_load_no_json_post():
    class app(morepath.App):
        pass

    class Root(object):
        pass

    @app.path(path='/', model=Root)
    def get_root():
        return Root()

    @app.json(model=Root, request_method='POST')
    def default(self, request):
        assert request.body_obj is None
        return 'done'

    c = Client(app())

    response = c.post('/', {'x': 'foo'})
    assert response.json == 'done'
