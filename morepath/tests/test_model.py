import urllib
from morepath.model import (register_root, register_model,
                            get_arguments, get_converters, get_url_parameters)
from morepath.converter import Converter, IDENTITY_CONVERTER
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
    config = setup()
    app = App(testing_config=config)
    root = Root()
    lookup = app.lookup()

    config.commit()

    register_root(app, Root, None, {}, lambda: root)
    assert generic.path(root, lookup=lookup) == ('', {})
    assert generic.app(root, lookup=lookup) is app


def test_register_model():
    config = setup()
    app = App(testing_config=config)
    root = Root()
    lookup = app.lookup()

    def get_model(id):
        model = Model()
        model.id = id
        return model

    config.commit()

    register_root(app, Root, None, {}, lambda: root)
    register_model(app, Model, '{id}', lambda model: {'id': model.id},
                   None, None, get_model)

    obj, request = consume(app, 'a')
    assert obj.id == 'a'
    model = Model()
    model.id = 'b'
    assert generic.path(model, lookup=lookup) == ('b', {})
    assert generic.app(model, lookup=lookup) is app


def test_register_model_with_parameters():
    config = setup()
    app = App(testing_config=config)
    root = Root()
    lookup = app.lookup()

    def get_model(id, param='default'):
        model = Model()
        model.id = id
        model.param = param
        return model

    config.commit()

    register_root(app, Root, None, {}, lambda: root)
    register_model(app, Model, '{id}', lambda model: {'id': model.id,
                                                      'param': model.param },
                   None, None, get_model)

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
    assert generic.app(model, lookup=lookup) is app


def test_traject_path_with_leading_slash():
    config = setup()
    app = App(testing_config=config)
    root = Root()

    def get_model(id):
        model = Model()
        model.id = id
        return model

    config.commit()

    register_root(app, Root, None, {}, lambda: root)
    register_model(app, Model, '/foo/{id}', lambda model: {'id': model.id},
                   None, None, get_model)
    obj, request = consume(app, 'foo/a')
    assert obj.id == 'a'
    obj, request = consume(app, '/foo/a')
    assert obj.id == 'a'


def test_get_arguments():
    def foo(a, b):
        pass
    assert get_arguments(foo, []) == { 'a': None, 'b': None }


def test_get_arguments_defaults():
    def foo(a, b=1):
        pass
    assert get_arguments(foo, []) == { 'a': None, 'b': 1 }


def test_get_arguments_exclude():
    def foo(a, b, request):
        pass
    assert get_arguments(foo, ['request']) == { 'a': None, 'b': None }


def test_get_converters_none_defaults():
    def converter_for_type(t):
        return IDENTITY_CONVERTER
    def converter_for_value(v):
        return IDENTITY_CONVERTER
    assert get_converters({'a': None}, {},
                          converter_for_type, converter_for_value) == {
        'a': IDENTITY_CONVERTER }


def test_get_converters_explicit():
    def converter_for_type(t):
        return IDENTITY_CONVERTER
    def converter_for_value(v):
        return IDENTITY_CONVERTER
    assert get_converters({'a': None}, {'a': Converter(int)},
                          converter_for_type, converter_for_value) == {
        'a': Converter(int) }

def test_get_converters_from_type():
    def converter_for_type(t):
        return Converter(int)
    def converter_for_value(v):
        return IDENTITY_CONVERTER
    assert get_converters({'a': None}, {'a': int},
                          converter_for_type, converter_for_value) == {
        'a': Converter(int) }
