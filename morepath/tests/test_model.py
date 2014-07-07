try:
    from urllib.parse import urlencode
except ImportError:
    # Python 2
    from urllib import urlencode
from morepath.path import register_path, get_arguments
from morepath.converter import Converter, IDENTITY_CONVERTER, ConverterRegistry
import morepath
from morepath import setup
from morepath import generic
from morepath.core import traject_consume
import webob


def setup_module(module):
    morepath.disable_implicit()


def consume(app, path, parameters=None):
    if parameters:
        path += '?' + urlencode(parameters, True)
    request = app.request(webob.Request.blank(path).environ)
    return traject_consume(request, app, lookup=app.lookup), request


class Root(object):
    pass


class Model(object):
    pass


def test_register_path():
    config = setup()

    class App(morepath.App):
        testing_config = config

    root = Root()

    app = App()
    lookup = app.lookup

    def get_model(id):
        model = Model()
        model.id = id
        return model

    config.commit()

    registry = app.registry

    register_path(registry, Root, '', lambda m: {},
                  None, None, None, False,
                  lambda: root)
    register_path(registry, Model, '{id}', lambda model: {'id': model.id},
                  None, None, None, False, get_model)
    registry.register(generic.context, [object], lambda obj: {})

    obj, request = consume(app, 'a')
    assert obj.id == 'a'
    model = Model()
    model.id = 'b'
    assert generic.path(model, lookup=lookup) == ('b', {})


def test_register_path_with_parameters():
    config = setup()

    class App(morepath.App):
        testing_config = config

    app = App()

    root = Root()
    lookup = app.lookup

    def get_model(id, param='default'):
        model = Model()
        model.id = id
        model.param = param
        return model

    config.commit()

    registry = app.registry

    register_path(registry, Root,  '', lambda m: {}, None, None, None, False,
                  lambda: root)
    register_path(registry, Model, '{id}',
                  lambda model: {'id': model.id, 'param': model.param},
                  None, None, None, False, get_model)
    registry.register(generic.context, [object], lambda obj: {})

    obj, request = consume(app, 'a')
    assert obj.id == 'a'
    assert obj.param == 'default'

    obj, request = consume(app, 'a', {'param': 'value'})
    assert obj.id == 'a'
    assert obj.param == 'value'

    model = Model()
    model.id = 'b'
    model.param = 'other'
    assert generic.path(model, lookup=lookup) == ('b', {'param': ['other']})


def test_traject_path_with_leading_slash():
    config = setup()

    class App(morepath.App):
        testing_config = config

    app = App()
    root = Root()

    def get_model(id):
        model = Model()
        model.id = id
        return model

    config.commit()

    registry = app.registry

    register_path(registry, Root, '', lambda m: {}, None, None, None, False,
                  lambda: root)
    register_path(registry, Model, '/foo/{id}', lambda model: {'id': model.id},
                  None, None, None, False, get_model)
    registry.register(generic.context, [object], lambda obj: {})

    obj, request = consume(app, 'foo/a')
    assert obj.id == 'a'
    obj, request = consume(app, '/foo/a')
    assert obj.id == 'a'


def test_get_arguments():
    def foo(a, b):
        pass
    assert get_arguments(foo, []) == {'a': None, 'b': None}


def test_get_arguments_defaults():
    def foo(a, b=1):
        pass
    assert get_arguments(foo, []) == {'a': None, 'b': 1}


def test_get_arguments_exclude():
    def foo(a, b, request):
        pass
    assert get_arguments(foo, ['request']) == {'a': None, 'b': None}


def test_argument_and_explicit_converters_none_defaults():
    class MyConverterRegistry(ConverterRegistry):
        def converter_for_type(self, t):
            return IDENTITY_CONVERTER

        def converter_for_value(self, v):
            return IDENTITY_CONVERTER

    reg = MyConverterRegistry()

    assert reg.argument_and_explicit_converters({'a': None}, {}) == {
        'a': IDENTITY_CONVERTER}


def test_argument_and_explicit_converters_explicit():
    class MyConverterRegistry(ConverterRegistry):
        def converter_for_type(self, t):
            return IDENTITY_CONVERTER

        def converter_for_value(self, v):
            return IDENTITY_CONVERTER

    reg = MyConverterRegistry()

    assert reg.argument_and_explicit_converters(
        {'a': None}, {'a': Converter(int)}) == {'a': Converter(int)}


def test_argument_and_explicit_converters_from_type():
    class MyConverterRegistry(ConverterRegistry):
        def converter_for_type(self, t):
            return Converter(int)

        def converter_for_value(self, v):
            return IDENTITY_CONVERTER

    reg = MyConverterRegistry()

    assert reg.argument_and_explicit_converters({'a': None}, {'a': int}) == {
        'a': Converter(int)}
