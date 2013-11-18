from morepath import config
from morepath.error import ConflictError
import pytest


def test_action():
    performed = []

    class MyAction(config.Action):
        def perform(self, obj):
            performed.append(obj)

        def discriminator(self):
            return ()

    c = config.Config()

    class Foo(object):
        pass

    foo = Foo()
    c.action(MyAction(), foo)
    assert performed == []
    c.commit()
    assert performed == [foo]


def test_action_not_implemented():
    class UnimplementedAction(config.Action):
        def discriminator(self):
            return None

    c = config.Config()
    c.action(UnimplementedAction(), None)
    with pytest.raises(NotImplementedError):
        c.commit()


def test_directive():
    performed = []

    class MyDirective(config.Directive):
        def perform(self, obj):
            performed.append(obj)

        def discriminator(self):
            return ()

    c = config.Config()

    d = MyDirective(None)

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
        def discriminator(self):
            return 1
    c = config.Config()

    a = MyDirective(None)

    @a
    def foo():
        pass

    b = MyDirective(None)

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


def test_different_apps_no_conflict():
    class MyDirective(config.Directive):
        def discriminator(self):
            return 1
        def perform(self, obj):
            pass

    c = config.Config()

    a = MyDirective('app_one')

    @a
    def foo():
        pass

    b = MyDirective('app_two')

    @b
    def bar():
        pass

    c.action(a, foo)
    c.action(b, bar)

    c.commit()


def test_multiple_discriminators_per_directive():
    class ADirective(config.Directive):
        def discriminator(self):
            return ['a', 1]

    class BDirective(config.Directive):
        def discriminator(self):
            return ['b', 1]

    c = config.Config()

    a = ADirective(None)

    @a
    def foo():
        pass

    b = BDirective(None)

    @b
    def bar():
        pass

    c.action(a, foo)
    c.action(b, bar)

    with pytest.raises(ConflictError):
        c.commit()
