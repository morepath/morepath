from morepath.traject import (is_identifier,
                              parse_variables,
                              create_variables_re,
                              VariableMatcher)
from morepath.pathstack import DEFAULT

# def test_variable_re():
#     assert variable_re.findall('foo {bar} {baz} hoi{qux}!') == 3

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

# def test_create_variables_re():
#     assert (create_variables_re('The {foo} is the {bar}.') ==
#             'The (.+) is the (.+).')

# def test_generalize_variables():
#     assert generalize_variables('No variables') == 'No variables'
#     assert (generalize_variables('The {foo} is the {bar}.') ==
#             'The (.+) is the (.+).')
    
def test_variable_matcher():
    matcher = VariableMatcher(DEFAULT, '{foo}')
    assert matcher((DEFAULT, 'test')) == {'foo': 'test'}
    matcher = VariableMatcher(DEFAULT, 'foo-{n}')
    assert matcher((DEFAULT, 'foo-bar')) == {'n': 'bar'}
    matcher = VariableMatcher(DEFAULT, 'hey')
    assert matcher((DEFAULT, 'hey')) == {}
    matcher = VariableMatcher(DEFAULT, 'foo-{n}')
    assert matcher((DEFAULT, 'blah')) == {}
