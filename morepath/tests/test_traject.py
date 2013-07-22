from morepath.traject import (is_identifier,
                              parse_variables,
                              create_variables_re,
                              VariableMatcher,
                              parse, Traject, TrajectConsumer)
from comparch import Registry
from morepath.pathstack import parse_path, DEFAULT
from morepath.interfaces import ITraject, TrajectError
import py.test

class Root(object):
    pass

class Model(object):
    pass

def test_identifier():
    assert is_identifier('a')
    not is_identifier('')
    assert is_identifier('a1')
    assert not is_identifier('1')
    assert is_identifier('_')
    assert is_identifier('_foo')
    assert is_identifier('foo')
    assert not is_identifier('.')

def test_parse_variables():
    assert parse_variables('No variables') == []
    assert parse_variables('The {foo} is the {bar}.') == ['foo', 'bar']
    assert parse_variables('{}') == ['']
    
def test_variable_matcher():
    matcher = VariableMatcher((DEFAULT, '{foo}'))
    assert matcher((DEFAULT, 'test')) == {'foo': 'test'}
    matcher = VariableMatcher((DEFAULT, 'foo-{n}'))
    assert matcher((DEFAULT, 'foo-bar')) == {'n': 'bar'}
    matcher = VariableMatcher((DEFAULT, 'hey'))
    assert matcher((DEFAULT, 'hey')) == {}
    matcher = VariableMatcher((DEFAULT, 'foo-{n}'))
    assert matcher((DEFAULT, 'blah')) == {}
    matcher = VariableMatcher((DEFAULT, '{ foo }'))
    assert matcher((DEFAULT, 'test')) == {'foo': 'test'}
    
def test_variable_matcher_ns():
    matcher = VariableMatcher((DEFAULT, '{foo}'))
    assert matcher(('not default', 'test')) == {}
    
def test_variable_matcher_checks():
    with py.test.raises(TrajectError):
        matcher = VariableMatcher((DEFAULT, '{1illegal}'))
    with py.test.raises(TrajectError):
        matcher = VariableMatcher((DEFAULT, '{}'))
        
def test_variable_matcher_type():
    matcher = VariableMatcher((DEFAULT, '{foo:str}'))
    assert matcher((DEFAULT, 'test')) == {'foo': 'test'}
    matcher = VariableMatcher((DEFAULT, '{foo:int}'))
    assert matcher((DEFAULT, '1')) == {'foo': 1}
    assert matcher((DEFAULT, 'noint')) == {}
    
def test_traject_consumer():
    reg = Registry()
    root = Root()
    traject = Traject()
    traject.register('sub', Model)
    reg.register(ITraject, (Root,), traject) 
    consumer = TrajectConsumer(reg)
    found, obj, stack = consumer(root, parse_path('sub'))
    assert found
    assert isinstance(obj, Model)
    assert stack == []

def test_traject_consumer_not_found():
    reg = Registry()
    root = Root()
    traject = Traject()
    reg.register(ITraject, (Root,), traject) 
    consumer = TrajectConsumer(reg)
    found, obj, stack = consumer(root, parse_path('sub'))
    assert not found
    assert obj is root
    assert stack == [(u'default', 'sub')]
    
def test_traject_consumer_no_traject():
    reg = Registry()
    root = Root()
    consumer = TrajectConsumer(reg)
    found, obj, stack = consumer(root, parse_path('sub'))
    assert not found
    assert obj is root
    assert stack == [(u'default', 'sub')]

def test_traject_consumer_variable():
    reg = Registry()
    root = Root()
    traject = Traject()
    def get_model(foo):
        result = Model()
        result.foo = foo
        return result
    traject.register('{foo}', get_model)
    reg.register(ITraject, (Root,), traject) 
    consumer = TrajectConsumer(reg)
    found, obj, stack = consumer(root, parse_path('something'))
    assert found
    assert isinstance(obj, Model)
    assert stack == []
    assert obj.foo == 'something'
    
def test_traject_consumer_combination():
    reg = Registry()
    root = Root()
    traject = Traject()
    def get_model(foo):
        result = Model()
        result.foo = foo
        return result
    class Special(object):
        pass
    traject.register('special', Special)
    traject.register('{foo}', get_model)
    reg.register(ITraject, (Root,), traject) 
    consumer = TrajectConsumer(reg)
    found, obj, stack = consumer(root, parse_path('something'))
    assert found
    assert isinstance(obj, Model)
    assert stack == []
    assert obj.foo == 'something'
    found, obj, stack = consumer(root, parse_path('special'))
    assert found
    assert isinstance(obj, Special)
    assert stack == []
    
