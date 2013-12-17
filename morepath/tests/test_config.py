from morepath import config
from morepath.error import ConflictError
import pytest


def test_action():
    performed = []

    class MyAction(config.Action):
        def perform(self, configurable, obj):
            performed.append(obj)

        def identifier(self):
            return ()

    c = config.Config()
    x = config.Configurable()

    class Foo(object):
        pass

    foo = Foo()
    c.configurable(x)
    c.action(MyAction(x), foo)
    assert performed == []
    c.commit()
    assert performed == [foo]


def test_action_priority():
    performed = []

    class MyAction(config.Action):
        def perform(self, configurable, obj):
            performed.append('myaction')

        def identifier(self):
            return ()

    class HighPriorityAction(config.Action):
        priority = 100
        def perform(self, configurable, obj):
            performed.append('highpriority')

        def identifier(self):
            return ('high',)

    c = config.Config()
    x = config.Configurable()

    class Foo(object):
        pass

    foo = Foo()
    bar = Foo()
    c.configurable(x)
    c.action(MyAction(x), foo)
    c.action(HighPriorityAction(x), bar)

    c.commit()
    assert performed == ['highpriority', 'myaction']


def test_action_not_implemented():
    class UnimplementedAction(config.Action):
        def identifier(self):
            return ()

    c = config.Config()
    x = config.Configurable()
    c.configurable(x)
    c.action(UnimplementedAction(x), None)
    with pytest.raises(NotImplementedError):
        c.commit()


def test_directive():
    performed = []

    class MyDirective(config.Directive):
        def perform(self, configurable, obj):
            performed.append(obj)

        def identifier(self):
            return ()

    c = config.Config()
    x = config.Configurable()

    c.configurable(x)

    d = MyDirective(x)

    # but this has no effect without scanning
    @d
    def foo():
        pass

    # so register action manually
    c.action(d, foo)

    c.commit()
    assert performed == [foo]


def test_conflict():
    class MyDirective(config.Directive):
        def identifier(self):
            return 1
    c = config.Config()
    x = config.Configurable()
    c.configurable(x)

    a = MyDirective(x)

    @a
    def foo():
        pass

    b = MyDirective(x)

    @b
    def bar():
        pass

    c.action(a, foo)
    c.action(b, bar)

    with pytest.raises(ConflictError):
        c.commit()

    try:
        c.commit()
    except ConflictError as e:
        s = str(e)
        # XXX how can we test more details? very dependent on code
        assert s.startswith('Conflict between:')


def test_different_configurables_no_conflict():
    class MyDirective(config.Directive):
        def identifier(self):
            return 1

        def perform(self, configurable, obj):
            pass

    c = config.Config()
    x1 = config.Configurable()
    x2 = config.Configurable()
    c.configurable(x1)
    c.configurable(x2)

    a = MyDirective(x1)

    @a
    def foo():
        pass

    b = MyDirective(x2)

    @b
    def bar():
        pass

    c.action(a, foo)
    c.action(b, bar)

    c.commit()


def test_extra_discriminators_per_directive():
    class ADirective(config.Directive):
        def identifier(self):
            return 'a'

        def discriminators(self):
            return [1]

    class BDirective(config.Directive):
        def identifier(self):
            return 'b'

        def discriminators(self):
            return [1]

    c = config.Config()
    x = config.Configurable()
    c.configurable(x)

    a = ADirective(x)

    @a
    def foo():
        pass

    b = BDirective(x)

    @b
    def bar():
        pass

    c.action(a, foo)
    c.action(b, bar)

    with pytest.raises(ConflictError):
        c.commit()


def test_configurable_inherit_without_change():
    performed = []

    class MyAction(config.Action):
        def perform(self, configurable, obj):
            performed.append((configurable, obj))

        def identifier(self):
            return ()

    c = config.Config()
    x = config.Configurable()
    y = config.Configurable(x)
    c.configurable(x)
    c.configurable(y)

    class Foo(object):
        pass

    foo = Foo()
    c.action(MyAction(x), foo)
    c.commit()

    assert performed == [(x, foo), (y, foo)]


def test_configurable_inherit_extending():
    a_performed = []
    b_performed = []

    class AAction(config.Action):
        def perform(self, configurable, obj):
            a_performed.append((configurable, obj))

        def identifier(self):
            return 'a_action'

    class BAction(config.Action):
        def perform(self, configurable, obj):
            b_performed.append((configurable, obj))

        def identifier(self):
            return 'b_action'

    c = config.Config()
    x = config.Configurable()
    y = config.Configurable(x)
    c.configurable(x)
    c.configurable(y)

    class Foo(object):
        pass

    foo = Foo()
    bar = Foo()
    c.action(AAction(x), foo)
    c.action(BAction(y), bar)
    c.commit()

    assert a_performed == [(x, foo), (y, foo)]
    assert b_performed == [(y, bar)]


def test_configurable_inherit_overriding():
    performed = []

    class MyAction(config.Action):
        def __init__(self, configurable, value):
            super(MyAction, self).__init__(configurable)
            self.value = value

        def perform(self, configurable, obj):
            performed.append((configurable, obj))

        def identifier(self):
            return 'action', self.value

    c = config.Config()
    x = config.Configurable()
    y = config.Configurable(x)
    c.configurable(x)
    c.configurable(y)

    class Foo(object):
        def __init__(self, name):
            self.name = name

        def __repr__(self):
            return '<Obj %s>' % self.name

    one = Foo('one')
    two = Foo('two')
    three = Foo('three')
    c.action(MyAction(x, 1), one)
    c.action(MyAction(x, 2), two)
    c.action(MyAction(y, 1), three)
    c.commit()

    assert performed == [(x, one), (x, two), (y, two), (y, three)]


def test_configurable_extra_discriminators():
    performed = []

    class MyAction(config.Action):
        def __init__(self, configurable, value, extra):
            super(MyAction, self).__init__(configurable)
            self.value = value
            self.extra = extra

        def perform(self, configurable, obj):
            performed.append((configurable, obj))

        def identifier(self):
            return 'action', self.value

        def discriminators(self):
            return [('extra', self.extra)]

    c = config.Config()
    x = config.Configurable()
    c.configurable(x)

    class Foo(object):
        def __init__(self, name):
            self.name = name

        def __repr__(self):
            return '<Obj %s>' % self.name

    one = Foo('one')
    two = Foo('two')
    three = Foo('three')
    c.action(MyAction(x, 1, 'a'), one)
    c.action(MyAction(x, 2, 'b'), two)
    c.action(MyAction(x, 3, 'b'), three)
    with pytest.raises(ConflictError):
        c.commit()


def test_prepare_returns_multiple_actions():
    performed = []

    class MyAction(config.Action):
        def __init__(self, configurable, value):
            super(MyAction, self).__init__(configurable)
            self.value = value

        def perform(self, configurable, obj):
            performed.append(obj)

        def identifier(self):
            return self.value

        def prepare(self, obj):
            yield MyAction(self.configurable, 1), obj
            yield MyAction(self.configurable, 2), obj

    c = config.Config()
    x = config.Configurable()

    class Foo(object):
        pass

    foo = Foo()
    c.configurable(x)
    c.action(MyAction(x, 3), foo)
    c.commit()
    assert performed == [foo, foo]


def test_abbreviation():
    performed = []

    class MyDirective(config.Directive):
        def __init__(self, configurable, foo=None, bar=None):
            super(MyDirective, self).__init__(configurable)
            self.foo = foo
            self.bar = bar

        def perform(self, configurable, obj):
            performed.append((obj, self.foo, self.bar))

        def identifier(self):
            return self.foo, self.bar

    c = config.Config()
    x = config.Configurable()

    c.configurable(x)

    with MyDirective(x, foo='blah') as d:
        d1 = d(bar='one')

        @d1
        def f1():
            pass
        c.action(d1, f1)

        d2 = d(bar='two')

        @d2
        def f2():
            pass
        c.action(d2, f2)

    c.commit()

    assert performed == [(f1, 'blah', 'one'), (f2, 'blah', 'two')]
