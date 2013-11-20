from morepath.model import register_root, register_model
from morepath.app import App, global_app
from werkzeug.test import EnvironBuilder
from morepath.request import Request
from morepath import setup
from morepath import generic
from morepath.traject import traject_consumer, parse_path


def setup_module(module):
    global_app.clear()


def get_request(*args, **kw):
    return Request(EnvironBuilder(*args, **kw).get_environ())


class Root(object):
    pass


class Model(object):
    pass


def test_register_root():
    app = App()
    root = Root()
    app.root_model = Root
    lookup = app.lookup()

    register_root(app, Root, lambda: root)
    request = get_request()
    request.lookup = lookup
    assert generic.path(request, root, lookup=lookup) == ''
    assert generic.base(root, lookup=lookup) is app


def test_register_model():
    setup()
    app = App()
    root = Root()
    app.root_model = Root
    lookup = app.lookup()

    def get_model(id):
        model = Model()
        model.id = id
        return model

    register_root(app, Root, lambda: root)
    register_model(app, Model, '{id}', lambda model: {'id': model.id},
                   get_model)

    found, obj, stack = traject_consumer(app, parse_path('a'), lookup)
    assert obj.id == 'a'
    model = Model()
    model.id = 'b'
    request = get_request()
    request.lookup = lookup
    assert generic.path(request, model, lookup=lookup) == 'b'
    assert generic.base(model, lookup=lookup) is app


def test_traject_path_with_leading_slash():
    setup()
    app = App()
    root = Root()
    app.root_model = Root
    lookup = app.lookup()

    def get_model(id):
        model = Model()
        model.id = id
        return model

    register_root(app, Root, lambda: root)
    register_model(app, Model, '/foo/{id}', lambda model: {'id': model.id},
                   get_model)
    found, obj, stack = traject_consumer(app, parse_path('foo/a'), lookup)
    assert obj.id == 'a'
    found, obj, stack = traject_consumer(app, parse_path('/foo/a'), lookup)
    assert obj.id == 'a'
