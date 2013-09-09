from morepath import config
import py.test

def test_action():
    performed = []
    class MyAction(config.Action):
        def perform(self, obj):
            performed.append(obj)
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
        pass
    c = config.Config()
    c.action(UnimplementedAction(), None)
    with py.test.raises(NotImplementedError):
        c.commit()

def test_directive():
    performed = []
    class MyDirective(config.Directive):
        def perform(self, obj):
            performed.append(obj)
    c = config.Config()

    d = MyDirective()

    # but this has no effect without scanning
    @d
    def foo():
        pass

    # so register action manually
    c.action(d, foo)

    c.commit()
    assert performed == [foo]
