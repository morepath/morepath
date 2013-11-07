from morepath.neotraject import Traject, Node, Step, TrajectError
import pytest

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


def test_variable_step():
    step = Step('{foo}')
    assert step.s == '{foo}'
    assert step.generalized == '{}'
    assert step.parts == ('', '')
    assert step.names == ['foo']
    assert step.converters == [str]
    assert step.has_variables()
    assert step.match('bar') == (True, {'foo': 'bar'})


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

def test_multi_mixed_step():
    step = Step('{foo}a{bar}')
    assert step.s == '{foo}a{bar}'
    assert step.generalized == '{}a{}'
    assert step.parts == ('', 'a', '')
    assert step.names == ['foo', 'bar']
    assert step.converters == [str, str]
    assert step.has_variables()


def test_converter():
    step = Step('{foo:int}')
    assert step.match('1') == (True, {'foo': 1})
    assert step.match('x') == (False, {})


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

