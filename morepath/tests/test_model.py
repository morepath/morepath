import urllib
from morepath.model import register_root, register_model
from morepath.app import App
from werkzeug.test import EnvironBuilder
from morepath import setup
from morepath import generic
from morepath.core import traject_consume


def consume(app, path, parameters=None):
    if parameters:
       path += '?' + urllib.urlencode(parameters, True)
    request = app.request(EnvironBuilder(path=path).get_environ())
    return traject_consume(request, app, lookup=app.lookup()), request


class Root(object):
    pass


class Model(object):
    pass


def test_register_root():
    app = App()
    root = Root()
    lookup = app.lookup()

    c = setup()
    c.configurable(app)
    c.commit()

    register_root(app, Root, lambda: root)
    assert generic.path(root, lookup=lookup) == ('', {})
    assert generic.base(root, lookup=lookup) is app


def test_register_model():
    app = App()
    root = Root()
    lookup = app.lookup()

    def get_model(id):
        model = Model()
        model.id = id
        return model

    c = setup()
    c.configurable(app)
    c.commit()

    register_root(app, Root, lambda: root)
    register_model(app, Model, '{id}', lambda model: {'id': model.id}, {},
                   get_model)

    obj, request = consume(app, 'a')
    assert obj.id == 'a'
    model = Model()
    model.id = 'b'
    assert generic.path(model, lookup=lookup) == ('b', {})
    assert generic.base(model, lookup=lookup) is app


def test_register_model_with_parameters():
    app = App()
    root = Root()
    lookup = app.lookup()

    def get_model(id, param):
        model = Model()
        model.id = id
        model.param = param
        return model

    c = setup()
    c.configurable(app)
    c.commit()

    register_root(app, Root, lambda: root)
    register_model(app, Model, '{id}', lambda model: {'id': model.id,
                                                      'param': model.param },
                   {'param': 'default'}, get_model)

    obj, request = consume(app, 'a')
    assert obj.id == 'a'
    assert obj.param == 'default'

    obj, request = consume(app, 'a', {'param': 'value'})
    assert obj.id == 'a'
    assert obj.param == 'value'

    model = Model()
    model.id = 'b'
    model.param = 'other'
    assert generic.path(model, lookup=lookup) == ('b', {'param': 'other'})
    assert generic.base(model, lookup=lookup) is app


def test_traject_path_with_leading_slash():
    app = App()
    root = Root()

    def get_model(id):
        model = Model()
        model.id = id
        return model

    c = setup()
    c.configurable(app)
    c.commit()

    register_root(app, Root, lambda: root)
    register_model(app, Model, '/foo/{id}', lambda model: {'id': model.id},
                   {}, get_model)
    obj, request = consume(app, 'foo/a')
    assert obj.id == 'a'
    obj, request = consume(app, '/foo/a')
    assert obj.id == 'a'
