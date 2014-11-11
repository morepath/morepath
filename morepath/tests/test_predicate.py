from morepath import Config
import reg
from reg import ClassIndex, KeyIndex
import morepath


def setup_module(module):
    morepath.disable_implicit()


def test_dispatch():
    config = Config()

    class App(morepath.App):
        testing_config = config

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @reg.dispatch('obj')
    def f(obj):
        return "fallback"

    @App.function(f, obj=Foo)
    def f_foo(obj):
        return "foo"

    @App.function(f, obj=Bar)
    def f_bar(obj):
        return "bar"

    config.commit()

    a = App()

    lookup = a.lookup

    assert f(Foo(), lookup=lookup) == 'foo'
    assert f(Bar(), lookup=lookup) == 'bar'
    assert f(Other(), lookup=lookup) == 'fallback'


def test_dispatch_external_predicates():
    config = Config()

    class App(morepath.App):
        testing_config = config

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @reg.dispatch_external_predicates()
    def f(obj):
        return "fallback"

    @App.predicate(f, name='model', default=None, index=ClassIndex)
    def f_obj(obj):
        return obj.__class__

    @App.function(f, model=Foo)
    def f_foo(obj):
        return "foo"

    @App.function(f, model=Bar)
    def f_bar(obj):
        return "bar"

    config.commit()

    a = App()

    lookup = a.lookup

    assert f(Foo(), lookup=lookup) == 'foo'
    assert f(Bar(), lookup=lookup) == 'bar'
    assert f(Other(), lookup=lookup) == 'fallback'


def test_dispatch_external_predicates_predicate_fallback():
    config = Config()

    class App(morepath.App):
        testing_config = config

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @reg.dispatch_external_predicates()
    def f(obj):
        return "dispatch function"

    @App.predicate(f, name='model', default=None, index=ClassIndex)
    def f_obj(obj):
        return obj.__class__

    @App.predicate_fallback(f, f_obj)
    def f_obj_fallback(obj):
        return "f_obj_fallback"

    @App.function(f, model=Foo)
    def f_foo(obj):
        return "foo"

    @App.function(f, model=Bar)
    def f_bar(obj):
        return "bar"

    config.commit()

    a = App()

    lookup = a.lookup

    assert f(Foo(), lookup=lookup) == 'foo'
    assert f(Bar(), lookup=lookup) == 'bar'
    assert f(Other(), lookup=lookup) == 'f_obj_fallback'


def test_dispatch_external_predicates_ordering_after():
    config = Config()

    class App(morepath.App):
        testing_config = config

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @reg.dispatch_external_predicates()
    def f(obj, name):
        return "fallback"

    @App.predicate(f, name='model', default=None, index=ClassIndex)
    def pred_obj(obj):
        return obj.__class__

    @App.predicate(f, name='name', default='', index=KeyIndex, after=pred_obj)
    def pred_name(name):
        return name

    @App.function(f, model=Foo, name='')
    def f_foo_default(obj, name):
        return "foo default"

    @App.function(f, model=Foo, name='edit')
    def f_foo_edit(obj, name):
        return "foo edit"

    @App.function(f, model=Bar, name='')
    def f_bar_default(obj, name):
        return "bar default"

    @App.function(f, model=Bar, name='edit')
    def f_bar_edit(obj, name):
        return "bar edit"

    config.commit()

    a = App()

    lookup = a.lookup

    assert f(Foo(), '', lookup=lookup) == 'foo default'
    assert f(Bar(), '', lookup=lookup) == 'bar default'
    assert f(Foo(), 'edit', lookup=lookup) == 'foo edit'
    assert f(Bar(), 'edit', lookup=lookup) == 'bar edit'

    assert f(Other(), '', lookup=lookup) == 'fallback'
    assert f(Other(), 'edit', lookup=lookup) == 'fallback'


def test_dispatch_external_predicates_ordering_before():
    config = Config()

    class App(morepath.App):
        testing_config = config

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @reg.dispatch_external_predicates()
    def f(obj, name):
        return "fallback"

    @App.predicate(f, name='name', default='', index=KeyIndex)
    def pred_name(name):
        return name

    @App.predicate(f, name='model', default=None, index=ClassIndex,
                   before=pred_name)
    def pred_obj(obj):
        return obj.__class__

    @App.function(f, model=Foo, name='')
    def f_foo_default(obj, name):
        return "foo default"

    @App.function(f, model=Foo, name='edit')
    def f_foo_edit(obj, name):
        return "foo edit"

    @App.function(f, model=Bar, name='')
    def f_bar_default(obj, name):
        return "bar default"

    @App.function(f, model=Bar, name='edit')
    def f_bar_edit(obj, name):
        return "bar edit"

    config.commit()

    a = App()

    lookup = a.lookup

    assert f(Foo(), '', lookup=lookup) == 'foo default'
    assert f(Bar(), '', lookup=lookup) == 'bar default'
    assert f(Foo(), 'edit', lookup=lookup) == 'foo edit'
    assert f(Bar(), 'edit', lookup=lookup) == 'bar edit'

    assert f(Other(), '', lookup=lookup) == 'fallback'
    assert f(Other(), 'edit', lookup=lookup) == 'fallback'
