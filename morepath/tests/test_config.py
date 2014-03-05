from morepath import config
from morepath.error import ConflictError
import pytest
import morepath


def setup_module(module):
    morepath.disable_implicit()


def test_action():
    performed = []

    class MyAction(config.Action):
        def perform(self, configurable, obj):
            performed.append(obj)

        def identifier(self, configurable):
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


def test_action_not_implemented():
    class UnimplementedAction(config.Action):
        def identifier(self, configurable):
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

        def identifier(self, configurable):
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


def test_directive_testing_config():
    performed = []

    class MyDirective(config.Directive):
        def perform(self, configurable, obj):
            performed.append(obj)

        def identifier(self, configurable):
            return ()

    c = config.Config()
    x = config.Configurable(testing_config=c)

    assert c.configurables == [x]

    # Due to testing_config, now the directive does work without scanning.
    @MyDirective(x)
    def foo():
        pass

    c.commit()
    assert performed == [foo]


def test_directive_without_testing_config_not_found():
    performed = []

    class MyDirective(config.Directive):
        def perform(self, configurable, obj):
            performed.append(obj)

        def identifier(self, configurable):
            return ()

    c = config.Config()
    x = config.Configurable()

    # The configurable won't be picked up.
    assert c.configurables == []

    # Since there's no testing_config, the directive does not get picked up,
    # as it isn't scanned.
    @MyDirective(x)
    def foo():
        pass

    c.commit()
    assert performed == []


def test_directive_testing_config_external():
    performed = []

    class MyDirective(config.Directive):
        def perform(self, configurable, obj):
            performed.append(obj)

        def identifier(self, configurable):
            return ()

    c = config.Config()
    x = config.Configurable()

    # we set up testing config later
    x.testing_config = c
    assert x.testing_config is c

    # even setting it up later will find us the configurable
    assert c.configurables == [x]

    # Due to testing_config, now the directive does work without scanning.
    @MyDirective(x)
    def foo():
        pass

    c.commit()
    assert performed == [foo]


def test_conflict():
    class MyDirective(config.Directive):
        def identifier(self, configurable):
            return 1
    c = config.Config()
    x = config.Configurable(testing_config=c)

    @MyDirective(x)
    def foo():
        pass

    @MyDirective(x)
    def bar():
        pass

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
        def identifier(self, configurable):
            return 1

        def perform(self, configurable, obj):
            pass

    c = config.Config()
    x1 = config.Configurable(testing_config=c)
    x2 = config.Configurable(testing_config=c)

    @MyDirective(x1)
    def foo():
        pass

    @MyDirective(x2)
    def bar():
        pass

    c.commit()


def test_extra_discriminators_per_directive():
    class ADirective(config.Directive):
        def __init__(self, configurable, v):
            super(ADirective, self).__init__(configurable)
            self.v = v

        def identifier(self, configurable):
            return 'a'

        def discriminators(self, configurable):
            return [self.v]

        def perform(self, configurable, obj):
            pass

    c = config.Config()
    x = config.Configurable(testing_config=c)

    @ADirective(x, 1)
    def foo():
        pass

    @ADirective(x, 1)
    def bar():
        pass

    with pytest.raises(ConflictError):
        c.commit()


def test_configurable_inherit_without_change():
    performed = []

    class MyAction(config.Action):
        def perform(self, configurable, obj):
            performed.append((configurable, obj))

        def identifier(self, configurable):
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

        def identifier(self, configurable):
            return 'a_action'

    class BAction(config.Action):
        def perform(self, configurable, obj):
            b_performed.append((configurable, obj))

        def identifier(self, configurable):
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

        def identifier(self, configurable):
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

        def identifier(self, configurable):
            return 'action', self.value

        def discriminators(self, configurable):
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

        def identifier(self, configurable):
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

        def identifier(self, configurable):
            return self.foo, self.bar

    c = config.Config()
    x = config.Configurable(testing_config=c)

    with MyDirective(x, foo='blah') as d:
        @d(bar='one')
        def f1():
            pass

        @d(bar='two')
        def f2():
            pass

    c.commit()

    assert performed == [(f1, 'blah', 'one'), (f2, 'blah', 'two')]


def test_config_phases():
    # when an action has a higher priority than another one,
    # we want it to be completely prepared and performed before
    # the other one even gets prepared and performed. This allows
    # directives that set up information that other directives use
    # during identifier and preparation stages (such as is the
    # case for view predicates)

    early_performed = []
    late_performed = []

    class EarlyAction(config.Action):
        def perform(self, configurable, obj):
            early_performed.append(obj)

        def identifier(self, configurable):
            return ('early',)

    class LateAction(config.Action):
        depends = [EarlyAction]

        # default priority
        def perform(self, configurable, obj):
            # make a copy of the early_performed list to
            # demonstrate it was already there when it's
            # in late_performed
            late_performed.append(list(early_performed))

        def identifier(self, configurable):
            # at this stage we already should have performed early
            assert early_performed == ['foo']
            return ('late')

    c = config.Config()
    x = config.Configurable()

    c.configurable(x)
    c.action(EarlyAction(x), 'foo')
    c.action(LateAction(x), 'bar')
    c.commit()
    assert early_performed == ['foo']
    assert late_performed == [['foo']]


def test_config_phases_extends():
    # when an action has a higher priority than another one,
    # we want it to be completely prepared and performed before
    # the other one even gets prepared and performed. This allows
    # directives that set up information that other directives use
    # during identifier and preparation stages (such as is the
    # case for view predicates)

    early_performed = []
    late_performed = []

    class EarlyAction(config.Action):
        def perform(self, configurable, obj):
            early_performed.append((configurable, obj))

        def identifier(self, configurable):
            return ('early',)

    class LateAction(config.Action):
        depends = [EarlyAction]

        # default priority
        def perform(self, configurable, obj):
            # make a copy of the early_performed list to
            # demonstrate it was already there when it's
            # in late_performed
            late_performed.append((configurable, list(early_performed)))

        def identifier(self, configurable):
            # at this stage we already should have performed early
            assert len(early_performed)
            return ('late',)

    c = config.Config()
    x = config.Configurable()
    y = config.Configurable(x)

    c.configurable(x)
    c.configurable(y)
    c.action(EarlyAction(x), 'foo')
    c.action(LateAction(y), 'bar')
    c.commit()
    assert early_performed == [(x, 'foo'), (y, 'foo')]
    assert late_performed == [(y, early_performed)]


def test_directive_on_method():
    performed = []

    class MyDirective(config.Directive):
        def __init__(self, configurable, foo=None):
            super(MyDirective, self).__init__(configurable)
            self.foo = foo

        def perform(self, configurable, obj):
            performed.append((obj, self.foo))

        def identifier(self, configurable):
            return self.foo

    c = config.Config()
    x = config.Configurable(testing_config=c)

    # This should error and does in Venusian mode,
    # but doesn't in testing_config mode.
    class Something(object):
        @MyDirective(x, 'A')
        def method():
            return "Result"


def test_directive_on_staticmethod():
    performed = []

    class MyDirective(config.Directive):
        def __init__(self, configurable, foo=None):
            super(MyDirective, self).__init__(configurable)
            self.foo = foo

        def perform(self, configurable, obj):
            performed.append((obj, self.foo))

        def identifier(self, configurable):
            return self.foo

    c = config.Config()
    x = config.Configurable(testing_config=c)

    # in Venusian code this will work, but we cannot support it in
    # testing_config mode, so we'll fail.
    with pytest.raises(config.DirectiveError):
        class Something(object):
            @MyDirective(x, 'A')
            @staticmethod
            def method():
                return 'result'


def test_directive_on_classmethod():
    performed = []

    class MyDirective(config.Directive):
        def __init__(self, configurable, foo=None):
            super(MyDirective, self).__init__(configurable)
            self.foo = foo

        def perform(self, configurable, obj):
            performed.append((obj, self.foo))

        def identifier(self, configurable):
            return self.foo

    c = config.Config()
    x = config.Configurable(testing_config=c)

    # in Venusian mode this will work, but we cannot support it in
    # testing_config mode so we'll fail.
    with pytest.raises(config.DirectiveError):
        class Something(object):
            @MyDirective(x, 'A')
            @classmethod
            def method(cls):
                return cls, 'result'


def test_configurable_actions():
    performed = []

    class MyAction(config.Action):
        def perform(self, configurable, obj):
            performed.append(obj)

        def identifier(self, configurable):
            return ()

    class App(config.Configurable):
        def actions(self):
            yield MyAction(self), self

    c = config.Config()
    x = App()

    c.configurable(x)
    assert performed == []
    c.commit()
    assert performed == [x]
