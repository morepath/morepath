from morepath.traject import (Traject, Node, Step, TrajectError,
                              is_identifier, parse_variables,
                              Path, traject_consumer,
                              parse_path, create_path)
from morepath import generic
from morepath.app import App, global_app
import pytest


class Root(object):
    pass


class Model(object):
    pass


class Special(object):
    pass


def test_name_step():
    step = Step('foo')
    assert step.s == 'foo'
    assert step.generalized == 'foo'
    assert step.parts == ('foo',)
    assert step.names == []
    assert step.converters == []
    assert not step.has_variables()
    assert step.match('foo') == (True, {})
    assert step.match('bar') == (False, {})
    assert step.discriminator_info() == 'foo'


def test_variable_step():
    step = Step('{foo}')
    assert step.s == '{foo}'
    assert step.generalized == '{}'
    assert step.parts == ('', '')
    assert step.names == ['foo']
    assert step.converters == [str]
    assert step.has_variables()
    assert step.match('bar') == (True, {'foo': 'bar'})
    assert step.discriminator_info() == '{str}'


def test_mixed_step():
    step = Step('a{foo}b')
    assert step.s == 'a{foo}b'
    assert step.generalized == 'a{}b'
    assert step.parts == ('a', 'b')
    assert step.names == ['foo']
    assert step.converters == [str]
    assert step.has_variables()
    assert step.match('abarb') == (True, {'foo': 'bar'})
    assert step.match('ab') == (False, {})
    assert step.match('xbary') == (False, {})
    assert step.match('yabarbx') == (False, {})
    assert step.match('afoo') == (False, {})
    assert step.discriminator_info() == 'a{str}b'


def test_multi_mixed_step():
    step = Step('{foo}a{bar}')
    assert step.s == '{foo}a{bar}'
    assert step.generalized == '{}a{}'
    assert step.parts == ('', 'a', '')
    assert step.names == ['foo', 'bar']
    assert step.converters == [str, str]
    assert step.has_variables()
    assert step.discriminator_info() == '{str}a{str}'


def test_converter():
    step = Step('{foo:int}')
    assert step.match('1') == (True, {'foo': 1})
    assert step.match('x') == (False, {})
    assert step.discriminator_info() == '{int}'


def sorted_steps(l):
    steps = [Step(s) for s in l]
    return [step.s for step in sorted(steps)]


def test_order_prefix_earlier():
    assert sorted_steps(['{foo}', 'prefix{foo}']) == [
        'prefix{foo}', '{foo}']


def test_order_postfix_earlier():
    assert sorted_steps(['{foo}', '{foo}postfix']) == [
        '{foo}postfix', '{foo}']


def test_order_prefix_before_postfix():
    assert sorted_steps(['{foo}', 'a{foo}', '{foo}a']) == [
        'a{foo}', '{foo}a', '{foo}']


def test_order_prefix_before_postfix2():
    assert sorted_steps(['{foo}', 'a{foo}', '{foo}b']) == [
        'a{foo}', '{foo}b', '{foo}']


def test_order_longer_prefix_before_shorter():
    assert sorted_steps(['ab{f}', 'a{f}']) == [
        'ab{f}', 'a{f}']


def test_order_longer_postfix_before_shorter():
    assert sorted_steps(['{f}ab', '{f}b']) == [
        '{f}ab', '{f}b']


def test_order_dont_care_variable_names():
    assert sorted_steps(['a{f}', 'ab{g}']) == [
        'ab{g}', 'a{f}']


def test_order_two_variables_before_one():
    assert sorted_steps(['{a}x{b}', '{a}']) == [
        '{a}x{b}', '{a}']


def test_order_two_variables_before_with_postfix():
    assert sorted_steps(['{a}x{b}x', '{a}x']) == [
        '{a}x{b}x', '{a}x']


def test_order_two_variables_before_with_prefix():
    assert sorted_steps(['x{a}x{b}', 'x{a}']) == [
        'x{a}x{b}', 'x{a}']


def test_order_two_variables_infix():
    assert sorted_steps(['{a}xyz{b}', '{a}xy{b}', '{a}yz{b}', '{a}x{b}',
                         '{a}z{b}', '{a}y{b}']) == [
        '{a}xyz{b}', '{a}yz{b}', '{a}z{b}', '{a}xy{b}', '{a}y{b}', '{a}x{b}']


def test_order_alphabetical():
    # reverse alphabetical
    assert sorted_steps(['a{f}', 'b{f}']) == [
        'b{f}', 'a{f}']
    assert sorted_steps(['{f}a', '{f}b']) == [
        '{f}b', '{f}a']


def test_invalid_step():
    with pytest.raises(TrajectError):
        Step('{foo')


def test_illegal_consecutive_variables():
    with pytest.raises(TrajectError):
        Step('{a}{b}')


def test_illegal_variable():
    with pytest.raises(TrajectError):
        Step('{a:int:int}')


def test_illegal_identifier():
    with pytest.raises(TrajectError):
        Step('{1}')


def test_unknown_converter():
    with pytest.raises(TrajectError):
        Step('{foo:blurb}')


def test_name_node():
    node = Node()
    step_node = node.add(Step('foo'))
    assert node.get('foo') == (step_node, {})
    assert node.get('bar') == (None, {})


def test_variable_node():
    node = Node()
    step_node = node.add(Step('{x}'))
    assert node.get('foo') == (step_node, {'x': 'foo'})
    assert node.get('bar') == (step_node, {'x': 'bar'})


def test_mixed_node():
    node = Node()
    step_node = node.add(Step('prefix{x}postfix'))
    assert node.get('prefixfoopostfix') == (step_node, {'x': 'foo'})
    assert node.get('prefixbarpostfix') == (step_node, {'x': 'bar'})
    assert node.get('prefixwhat') == (None, {})


def test_variable_node_specific_first():
    node = Node()
    x_node = node.add(Step('{x}'))
    prefix_node = node.add(Step('prefix{x}'))
    assert node.get('what') == (x_node, {'x': 'what'})
    assert node.get('prefixwhat') == (prefix_node, {'x': 'what'})


def test_variable_node_more_specific_first():
    node = Node()
    xy_node = node.add(Step('x{x}y'))
    xay_node = node.add(Step('xa{x}y'))
    ay_node = node.add(Step('a{x}y'))
    assert node.get('xwhaty') == (xy_node, {'x': 'what'})
    assert node.get('xawhaty') == (xay_node, {'x': 'what'})
    assert node.get('awhaty') == (ay_node, {'x': 'what'})


def test_traject_simple():
    traject = Traject()
    traject.add_pattern('a/b/c', 'abc')
    traject.add_pattern('a/b/d', 'abd')
    traject.add_pattern('x/y', 'xy')
    traject.add_pattern('x/z', 'xz')

    assert traject(['c', 'b', 'a']) == ('abc', [], {})
    assert traject(['d', 'b', 'a']) == ('abd', [], {})
    assert traject(['y', 'x']) == ('xy', [], {})
    assert traject(['z', 'x']) == ('xz', [], {})
    assert traject(['d', 'c', 'b', 'a']) == ('abc', ['d'], {})
    assert traject(['d', 'd', 'b', 'a']) == ('abd', ['d'], {})
    assert traject(['3', '2', '1', 'y', 'x']) == ('xy', ['3', '2', '1'], {})
    assert traject(['3', '2', '1']) == (None, ['3', '2', '1'], {})
    assert traject(['b', 'a']) == (None, [], {})


def test_traject_variable_specific_first():
    traject = Traject()
    traject.add_pattern('a/{x}/b', 'axb')
    traject.add_pattern('a/prefix{x}/b', 'aprefixxb')
    assert traject(['b', 'lah', 'a']) == ('axb', [], {'x': 'lah'})
    assert traject(['b', 'prefixlah', 'a']) == ('aprefixxb', [], {'x': 'lah'})


def test_traject_multiple_steps_with_variables():
    traject = Traject()
    traject.add_pattern('{x}/{y}', 'xy')
    assert traject(['y', 'x']) == ('xy', [], {'x': 'x', 'y': 'y'})


def test_traject_with_converter():
    traject = Traject()
    traject.add_pattern('{x:int}', 'found')
    assert traject(['1']) == ('found', [], {'x': 1})
    assert traject(['foo']) == (None, ['foo'], {})


def test_traject_with_converter_and_fallback():
    traject = Traject()
    traject.add_pattern('{x:int}', 'found_int')
    traject.add_pattern('{x:str}', 'found_str')

    assert traject(['1']) == ('found_int', [], {'x': 1})
    assert traject(['foo']) == ('found_str', [], {'x': 'foo'})


def test_traject_with_converter_and_fallback2():
    traject = Traject()
    traject.add_pattern('{x}', 'found_str')
    traject.add_pattern('{x:int}', 'found_int')

    assert traject(['1']) == ('found_int', [], {'x': 1})
    assert traject(['foo']) == ('found_str', [], {'x': 'foo'})


def test_traject_with_converter_and_fallback3():
    traject = Traject()
    # XXX should have a conflict
    traject.add_pattern('{x:str}', 'found_explicit')
    traject.add_pattern('{x}', 'found_implicit')

    assert traject(['foo']) == ('found_explicit', [], {'x': 'foo'})


def test_traject_greedy_middle_converter():
    traject = Traject()
    traject.add_pattern('a/{x:int}/y', 'int')
    traject.add_pattern('a/{x}/z', 'str')

    assert traject(['y', '1', 'a']) == ('int', [], {'x': 1})
    assert traject(['z', '1', 'a']) == (None,  ['z'], {'x': 1})
    assert traject(['z', 'x', 'a']) == ('str', [], {'x': 'x'})


def test_traject_greedy_middle_prefix():
    traject = Traject()
    traject.add_pattern('a/prefix{x}/y', 'prefix')
    traject.add_pattern('a/{x}/z', 'no_prefix')

    assert traject(['y', 'prefixX', 'a']) == ('prefix', [], {'x': 'X'})
    assert traject(['z', 'prefixX', 'a']) == (None, ['z'], {'x': 'X'})
    assert traject(['z', 'blah', 'a']) == ('no_prefix', [], {'x': 'blah'})


def test_traject_greedy_middle_converter_2():
    traject = Traject()
    traject.add_pattern('a/{x:int}/y', 'int')
    traject.add_pattern('a/{x}', 'str')

    assert traject(['y', '1', 'a']) == ('int', [], {'x': 1})
    # this greedily goes into the int branch, and then doesn't find it
    assert traject(['1', 'a']) == (None,  [], {'x': 1})
    # this works however for non-int
    assert traject(['blah', 'a']) == ('str', [], {'x': 'blah'})


def test_parse_path():
    assert parse_path(u'/a/b/c') == ['c', 'b', 'a']


def test_parse_path_empty():
    assert parse_path(u'') == []


def test_parse_path_slash():
    assert parse_path(u'/') == []


def test_parse_path_no_slash():
    assert parse_path('a/b/c') == ['c', 'b', 'a']


def test_parse_path_end_slash():
    assert parse_path('a/b/c/') == ['c', 'b', 'a']


def test_parse_path_multi_slash():
    assert parse_path(u'/a/b/c') == parse_path(u'/a//b/c')
    assert parse_path(u'/a/b/c') == parse_path(u'/a///b/c')


def test_create_path():
    assert create_path(['c', 'b', 'a']) == '/a/b/c'


# XXX removing /./ from paths and checking for ../


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
    assert parse_variables('No variables') == ([], [])
    assert parse_variables('The {foo} is the {bar}.') == (
        ['foo', 'bar'], [str, str])
    with pytest.raises(TrajectError):
        parse_variables('{}')
    with pytest.raises(TrajectError):
        parse_variables('{1illegal}')


def test_traject_consumer():
    app = App()
    traject = Traject()
    traject.add_pattern('sub', Model)
    app.register(generic.traject, [App], lambda base: traject)
    found, obj, stack = traject_consumer(app, ['sub'], app.lookup())
    assert found
    assert isinstance(obj, Model)
    assert stack == []


def test_traject_consumer_not_found():
    app = App()
    found, obj, stack = traject_consumer(app, ['sub'], app.lookup())
    assert not found
    assert obj is app
    assert stack == ['sub']


def test_traject_consumer_factory_returns_none():
    app = App()

    traject = Traject()

    def get_model():
        return None

    traject.add_pattern('sub', get_model)
    app.register(generic.traject, [App], lambda base: traject)

    found, obj, stack = traject_consumer(app, ['sub'], app.lookup())

    assert not found
    assert obj is app
    assert stack == ['sub']


def test_traject_consumer_variable():
    app = App()

    traject = Traject()

    def get_model(foo):
        result = Model()
        result.foo = foo
        return result

    traject.add_pattern('{foo}', get_model)
    app.register(generic.traject, [App], lambda base: traject)

    found, obj, stack = traject_consumer(app, ['something'],
                                         app.lookup())
    assert found
    assert isinstance(obj, Model)
    assert stack == []
    assert obj.foo == 'something'


def test_traject_consumer_view():
    app = App()

    traject = Traject()

    def get_model(foo):
        result = Model()
        result.foo = foo
        return result

    traject.add_pattern('', Root)
    traject.add_pattern('{foo}', get_model)
    app.register(generic.traject, [App], lambda base: traject)

    found, obj, stack = traject_consumer(app, ['+something'],
                                         app.lookup())
    assert found
    assert isinstance(obj, Root)
    assert stack == ['+something']


def test_traject_root():
    app = App()

    traject = Traject()

    traject.add_pattern('', Root)
    app.register(generic.traject, [App], lambda base: traject)

    found, obj, stack = traject_consumer(app, [],
                                         app.lookup())
    assert found
    assert isinstance(obj, Root)
    assert stack == []


def test_traject_consumer_combination():
    app = App()

    traject = Traject()

    def get_model(foo):
        result = Model()
        result.foo = foo
        return result

    traject.add_pattern('special', Special)
    traject.add_pattern('{foo}', get_model)
    app.register(generic.traject, [App], lambda base: traject)

    found, obj, stack = traject_consumer(app, ['something'],
                                         app.lookup())
    assert found
    assert isinstance(obj, Model)
    assert stack == []
    assert obj.foo == 'something'
    found, obj, stack = traject_consumer(app, ['special'],
                                         app.lookup())
    assert found
    assert isinstance(obj, Special)
    assert stack == []


def test_traject_nested():
    app = App()

    traject = Traject()
    traject.add_pattern('a', Model)
    traject.add_pattern('a/b', Special)
    app.register(generic.traject, [App], lambda base: traject)

    found, obj, stack = traject_consumer(app, ['a'], app.lookup())
    assert found
    assert isinstance(obj, Model)
    assert stack == []
    found, obj, stack = traject_consumer(app, ['b', 'a'], app.lookup())
    assert found
    assert isinstance(obj, Special)
    assert stack == []


def test_traject_nested_not_resolved_entirely_by_consumer():
    app = App()
    traject = Traject()
    traject.add_pattern('a', Model)
    app.register(generic.traject, [App], lambda base: traject)

    found, obj, stack = traject_consumer(app, ['a'], app.lookup())
    assert found
    assert isinstance(obj, Model)
    assert stack == []
    found, obj, stack = traject_consumer(app, ['b', 'a'], app.lookup())
    assert found
    assert isinstance(obj, Model)
    assert stack == ['b']


def test_traject_nested_with_variable():
    app = App()

    traject = Traject()

    def get_model(id):
        result = Model()
        result.id = id
        return result

    def get_special(id):
        result = Special()
        result.id = id
        return result

    traject.add_pattern('{id}', get_model)
    traject.add_pattern('{id}/sub', get_special)
    app.register(generic.traject, [App], lambda base: traject)

    found, obj, stack = traject_consumer(app, ['a'], app.lookup())
    assert found
    assert isinstance(obj, Model)
    assert stack == []
    found, obj, stack = traject_consumer(app, ['b'], app.lookup())
    assert found
    assert isinstance(obj, Model)
    assert stack == []
    found, obj, stack = traject_consumer(app, ['sub', 'a'], app.lookup())
    assert found
    assert isinstance(obj, Special)
    assert stack == []


def test_traject_with_multiple_variables():
    app = App()

    traject = Traject()

    def get_model(first_id):
        result = Model()
        result.first_id = first_id
        return result

    def get_special(first_id, second_id):
        result = Special()
        result.first_id = first_id
        result.second_id = second_id
        return result
    traject.add_pattern('{first_id}', get_model)
    traject.add_pattern('{first_id}/{second_id}', get_special)
    app.register(generic.traject, [App], lambda base: traject)

    found, obj, stack = traject_consumer(app, ['a'], app.lookup())
    assert found
    assert isinstance(obj, Model)
    assert stack == []
    assert obj.first_id == 'a'
    assert not hasattr(obj, 'second_id')
    found, obj, stack = traject_consumer(app, ['b', 'a'], app.lookup())
    assert found
    assert isinstance(obj, Special)
    assert stack == []
    assert obj.first_id == 'a'
    assert obj.second_id == 'b'


def test_traject_no_concecutive_variables():
    traject = Traject()

    with pytest.raises(TrajectError):
        traject.add_pattern('{foo}{bar}', 'value')


def test_traject_no_duplicate_variables():
    traject = Traject()

    with pytest.raises(TrajectError):
        traject.add_pattern('{foo}-{foo}', 'value')
    with pytest.raises(TrajectError):
        traject.add_pattern('{foo}/{foo}', 'value')


def test_interpolation_str():
    assert Path('{foo} is {bar}').interpolation_str() == '%(foo)s is %(bar)s'


def test_interpolation_str_with_converters():
    assert Path('{foo:int}').interpolation_str() == '%(foo)s'


def test_path_for_model():
    traject = Traject()

    class IdModel(object):
        def __init__(self, id):
            self.id = id

    traject.inverse(IdModel, 'foo/{id}',
                    lambda model: {'id': model.id})
    assert traject.path(IdModel('a')) == 'foo/a'


def test_path_for_model_with_converter():
    traject = Traject()

    class IdModel(object):
        def __init__(self, id):
            self.id = id

    traject.inverse(IdModel, 'foo/{id:int}',
                    lambda model: {'id': model.id})
    assert traject.path(IdModel(1)) == 'foo/1'


def test_path_discriminator():
    p = Path('/foo/{x:int}/bar/{y}')
    assert p.discriminator() == 'foo/{int}/bar/{str}'
