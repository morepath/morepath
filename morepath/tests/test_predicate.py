from morepath.app import App
from morepath import setup, Config
import reg
from reg import match_argname, ClassIndex, KeyIndex
import morepath


def setup_module(module):
    morepath.disable_implicit()


def test_dispatch():
    config = Config()

    class app(App):
        testing_config = config

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @reg.dispatch(match_argname('obj'))
    def f(obj):
        return "fallback"

    @app.function(f, Foo)
    def f_foo(obj):
        return "foo"

    @app.function(f, Bar)
    def f_bar(obj):
        return "bar"

    config.commit()

    a = app()

    lookup = a.lookup

    assert f(Foo(), lookup=lookup) == 'foo'
    assert f(Bar(), lookup=lookup) == 'bar'
    assert f(Other(), lookup=lookup) == 'fallback'


def test_dispatch_external_predicates():
    config = Config()

    class app(App):
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

    @app.predicate(f, name='model', default=None, index=ClassIndex)
    def f_obj(obj):
        return obj.__class__

    @app.function(f, Foo)
    def f_foo(obj):
        return "foo"

    @app.function(f, Bar)
    def f_bar(obj):
        return "bar"

    config.commit()

    a = app()

    lookup = a.lookup

    assert f(Foo(), lookup=lookup) == 'foo'
    assert f(Bar(), lookup=lookup) == 'bar'
    assert f(Other(), lookup=lookup) == 'fallback'


def test_dispatch_external_predicates_predicate_fallback():
    config = Config()

    class app(App):
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

    @app.predicate(f, name='model', default=None, index=ClassIndex)
    def f_obj(obj):
        return obj.__class__

    @app.predicate_fallback(f, f_obj)
    def f_obj_fallback(obj):
        return "f_obj_fallback"

    @app.function(f, Foo)
    def f_foo(obj):
        return "foo"

    @app.function(f, Bar)
    def f_bar(obj):
        return "bar"

    config.commit()

    a = app()

    lookup = a.lookup

    assert f(Foo(), lookup=lookup) == 'foo'
    assert f(Bar(), lookup=lookup) == 'bar'
    assert f(Other(), lookup=lookup) == 'f_obj_fallback'


def test_dispatch_external_predicates_ordering_after():
    config = Config()

    class app(App):
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

    @app.predicate(f, name='model', default=None, index=ClassIndex)
    def pred_obj(obj):
        return obj.__class__

    @app.predicate(f, name='name', default='', index=KeyIndex, after=pred_obj)
    def pred_name(name):
        return name

    @app.function(f, Foo, '')
    def f_foo_default(obj, name):
        return "foo default"

    @app.function(f, Foo, 'edit')
    def f_foo_edit(obj, name):
        return "foo edit"

    @app.function(f, Bar, '')
    def f_bar_default(obj, name):
        return "bar default"

    @app.function(f, Bar, 'edit')
    def f_bar_edit(obj, name):
        return "bar edit"

    config.commit()

    a = app()

    lookup = a.lookup

    assert f(Foo(), '', lookup=lookup) == 'foo default'
    assert f(Bar(), '', lookup=lookup) == 'bar default'
    assert f(Foo(), 'edit', lookup=lookup) == 'foo edit'
    assert f(Bar(), 'edit', lookup=lookup) == 'bar edit'

    assert f(Other(), '', lookup=lookup) == 'fallback'
    assert f(Other(), 'edit', lookup=lookup) == 'fallback'


def test_dispatch_external_predicates_ordering_before():
    config = Config()

    class app(App):
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

    @app.predicate(f, name='name', default='', index=KeyIndex)
    def pred_name(name):
        return name

    @app.predicate(f, name='model', default=None, index=ClassIndex,
                   before=pred_name)
    def pred_obj(obj):
        return obj.__class__

    @app.function(f, Foo, '')
    def f_foo_default(obj, name):
        return "foo default"

    @app.function(f, Foo, 'edit')
    def f_foo_edit(obj, name):
        return "foo edit"

    @app.function(f, Bar, '')
    def f_bar_default(obj, name):
        return "bar default"

    @app.function(f, Bar, 'edit')
    def f_bar_edit(obj, name):
        return "bar edit"

    config.commit()

    a = app()

    lookup = a.lookup

    assert f(Foo(), '', lookup=lookup) == 'foo default'
    assert f(Bar(), '', lookup=lookup) == 'bar default'
    assert f(Foo(), 'edit', lookup=lookup) == 'foo edit'
    assert f(Bar(), 'edit', lookup=lookup) == 'bar edit'

    assert f(Other(), '', lookup=lookup) == 'fallback'
    assert f(Other(), 'edit', lookup=lookup) == 'fallback'
