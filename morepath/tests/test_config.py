from morepath import config
import py.test

def test_action():
    performed = []
    class MyAction(config.Action):
        def perform(self, name, obj):
            performed.append((name, obj))
    c = config.Config()
    class Foo(object):
        pass
    foo = Foo()
    c.action(MyAction(), 'foo', foo)
    assert performed == []
    c.commit()
    assert performed == [('foo', foo)]


def test_action_not_implemented():
    class UnimplementedAction(config.Action):
        pass
    c = config.Config()
    c.action(UnimplementedAction(), 'foo', None)
    with py.test.raises(NotImplementedError):
        c.commit()
