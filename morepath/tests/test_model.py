import urllib
from morepath.model import (register_root, register_model,
                            variables_from_arginfo, parameters_from_arginfo)
from morepath.app import App
from werkzeug.test import EnvironBuilder
from morepath import setup
from morepath import generic
from morepath.core import traject_consume
import pytest

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

    register_root(app, Root, None, {}, lambda: root)
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

    register_root(app, Root, None, {}, lambda: root)
    register_model(app, Model, '{id}', lambda model: {'id': model.id}, None,
                   {}, get_model)

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

    register_root(app, Root, None, {}, lambda: root)
    register_model(app, Model, '{id}', lambda model: {'id': model.id,
                                                      'param': model.param },
                   None, {'param': 'default'}, get_model)

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

    register_root(app, Root, None, {}, lambda: root)
    register_model(app, Model, '/foo/{id}', lambda model: {'id': model.id},
                   None, {}, get_model)
    obj, request = consume(app, 'foo/a')
    assert obj.id == 'a'
    obj, request = consume(app, '/foo/a')
    assert obj.id == 'a'


def test_variables_from_arginfo():
    class Model(object):
        def __init__(self, a, b):
            self.a = a
            self.b = b
    variables = variables_from_arginfo(Model)
    assert variables(Model('A', 'B')) == {'a': 'A', 'b': 'B'}
    class WrongModel(object):
        pass
    with pytest.raises(AttributeError):
        variables(WrongModel())


def test_variables_from_arginfo_with_base_request():
    class Model(object):
        def __init__(self, a, b, base, request):
            self.a = a
            self.b = b
    variables = variables_from_arginfo(Model)
    assert variables(Model('A', 'B',
                           request=None, base=None)) == {'a': 'A', 'b': 'B'}


def test_parameters_from_arginfo():
    def foo(a, b):
        pass
    assert parameters_from_arginfo('foo/{a}', foo) == {
        'b': None
        }


def test_parameters_from_arginfo_with_base_request():
    def foo(a, b, base, request):
        pass
    assert parameters_from_arginfo('foo/{a}', foo) == {
        'b': None
        }
