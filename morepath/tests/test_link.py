import pytest

from morepath.app import App
from morepath.converter import Converter


@pytest.fixture
def info():
    class MyApp(App):
        pass

    MyApp.commit()

    app = MyApp()
    r = app.config.path_registry
    return app, r


def test_path_without_variables(info):
    app, r = info

    class Foo(object):
        pass

    r.register_inverse_path(model=Foo,
                            path='/',
                            factory_args=set())
    info = app._get_path(Foo())
    assert info.path == ''
    assert info.parameters == {}


def test_path_with_variables(info):
    app, r = info

    class Foo(object):
        def __init__(self, name):
            self.name = name

    r.register_path_variables(Foo,
                              lambda obj: {'name': obj.name})
    r.register_inverse_path(model=Foo,
                            path='/foos/{name}',
                            factory_args=set(['name']))
    info = app._get_path(Foo('a'))
    assert info.path == 'foos/a'
    assert info.parameters == {}


def test_path_with_default_variables(info):
    app, r = info

    class Foo(object):
        def __init__(self, name):
            self.name = name

    r.register_inverse_path(model=Foo,
                            path='/foos/{name}',
                            factory_args=set(['name']))
    info = app._get_path(Foo('a'))
    assert info.path == 'foos/a'
    assert info.parameters == {}


def test_path_with_parameters(info):
    app, r = info

    class Foo(object):
        def __init__(self, name):
            self.name = name

    r.register_path_variables(Foo,
                              lambda obj: {'name': obj.name})
    r.register_inverse_path(model=Foo,
                            path='/foos',
                            factory_args=set(['name']))
    info = app._get_path(Foo('a'))
    assert info.path == 'foos'
    assert info.parameters == {'name': ['a']}


def test_class_path_without_variables(info):
    app, r = info

    class Foo(object):
        pass

    r.register_inverse_path(model=Foo,
                            path='/',
                            factory_args=set())
    info = app._class_path(Foo, {})
    assert info.path == ''
    assert info.parameters == {}


def test_class_path_with_variables(info):
    app, r = info

    class Foo(object):
        def __init__(self, name):
            self.name = name

    r.register_inverse_path(model=Foo,
                            path='/foos/{name}',
                            factory_args=set(['name']))
    info = app._class_path(Foo, {'name': 'a'})
    assert info.path == 'foos/a'
    assert info.parameters == {}


def test_class_path_with_parameters(info):
    app, r = info

    class Foo(object):
        def __init__(self, name):
            self.name = name

    r.register_inverse_path(model=Foo,
                            path='/foos',
                            factory_args=set(['name']))
    info = app._class_path(Foo, {'name': 'a'})
    assert info.path == 'foos'
    assert info.parameters == {'name': ['a']}


def test_class_path_variables_with_converters(info):
    app, r = info

    class Foo(object):
        def __init__(self, value):
            self.value = value
    r.register_inverse_path(model=Foo,
                            path='/foos/{value}',
                            factory_args=set(['value']),
                            converters={'value': Converter(int)})
    info = app._class_path(Foo, {'value': 1})
    assert info.path == 'foos/1'
    assert info.parameters == {}


def test_class_path_parameters_with_converters(info):
    app, r = info

    class Foo(object):
        def __init__(self, value):
            self.value = value
    r.register_inverse_path(model=Foo,
                            path='/foos',
                            factory_args=set(['value']),
                            converters={'value': Converter(int)})
    info = app._class_path(Foo, {'value': 1})
    assert info.path == 'foos'
    assert info.parameters == {'value': ['1']}


def test_class_path_absorb(info):
    app, r = info

    class Foo(object):
        pass

    r.register_inverse_path(model=Foo,
                            path='/foos',
                            factory_args=set(),
                            absorb=True)
    info = app._class_path(Foo, {'absorb': 'bar'})
    assert info.path == 'foos/bar'
    assert info.parameters == {}


def test_class_path_extra_parameters(info):
    app, r = info

    class Foo(object):
        pass

    r.register_inverse_path(model=Foo,
                            path='/foos',
                            factory_args=set())
    info = app._class_path(Foo, {'extra_parameters': {'a': 'A',
                                                      'b': 'B'}})
    assert info.path == 'foos'
    assert info.parameters == {'a': ['A'], 'b': ['B']}


def test_class_path_extra_parameters_convert(info):
    app, r = info

    class Foo(object):
        pass

    r.register_inverse_path(model=Foo,
                            path='/foos',
                            factory_args=set(),
                            converters={'a': Converter(int)})
    info = app._class_path(Foo,
                           {'extra_parameters': {'a': 1,
                                                 'b': 'B'}})
    assert info.path == 'foos'
    assert info.parameters == {'a': ['1'], 'b': ['B']}
