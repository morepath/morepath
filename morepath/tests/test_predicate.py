from reg import ClassIndex, KeyIndex
import morepath
from morepath.error import ConfigError
from morepath.dispatch import delegate
import pytest


def test_dispatch():
    class App(morepath.App):
        @delegate('obj')
        def f(self, obj):
            return "fallback"

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.function(App.f, obj=Foo)
    def f_foo(app, obj):
        return "foo"

    @App.function(App.f, obj=Bar)
    def f_bar(obj):
        return "bar"

    a = App()

    a.commit()

    assert a.f(Foo()) == 'foo'
    assert a.f(Bar()) == 'bar'
    assert a.f(Other()) == 'fallback'


def test_dispatch_external_predicates():
    class App(morepath.App):

        @delegate.on_external_predicates()
        def f(self, obj):
            return "fallback"

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.predicate(App.f, name='model', default=None, index=ClassIndex)
    def f_obj(obj):
        return obj.__class__

    @App.function(App.f, model=Foo)
    def f_foo(obj):
        return "foo"

    @App.function(App.f, model=Bar)
    def f_bar(obj):
        return "bar"

    a = App()
    a.commit()

    assert a.f(Foo()) == 'foo'
    assert a.f(Bar()) == 'bar'
    assert a.f(Other()) == 'fallback'


def test_dispatch_external_predicates_predicate_fallback():
    class App(morepath.App):
        @delegate.on_external_predicates()
        def f(self, obj):
            return "dispatch function"

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.predicate(App.f, name='model', default=None, index=ClassIndex)
    def f_obj(obj):
        return obj.__class__

    @App.predicate_fallback(App.f, f_obj)
    def f_obj_fallback(obj):
        return "f_obj_fallback"

    @App.function(App.f, model=Foo)
    def f_foo(obj):
        return "foo"

    @App.function(App.f, model=Bar)
    def f_bar(obj):
        return "bar"

    a = App()
    a.commit()

    assert a.f(Foo()) == 'foo'
    assert a.f(Bar()) == 'bar'
    assert a.f(Other()) == 'f_obj_fallback'


def test_dispatch_external_predicates_ordering_after():
    class App(morepath.App):
        @delegate.on_external_predicates()
        def f(self, obj, name):
            return "fallback"

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.predicate(App.f, name='model', default=None, index=ClassIndex)
    def pred_obj(obj):
        return obj.__class__

    @App.predicate(App.f, name='name', default='',
                   index=KeyIndex, after=pred_obj)
    def pred_name(name):
        return name

    @App.function(App.f, model=Foo, name='')
    def f_foo_default(obj, name):
        return "foo default"

    @App.function(App.f, model=Foo, name='edit')
    def f_foo_edit(obj, name):
        return "foo edit"

    @App.function(App.f, model=Bar, name='')
    def f_bar_default(obj, name):
        return "bar default"

    @App.function(App.f, model=Bar, name='edit')
    def f_bar_edit(obj, name):
        return "bar edit"

    a = App()
    a.commit()

    assert a.f(Foo(), '') == 'foo default'
    assert a.f(Bar(), '') == 'bar default'
    assert a.f(Foo(), 'edit') == 'foo edit'
    assert a.f(Bar(), 'edit') == 'bar edit'

    assert a.f(Other(), '') == 'fallback'
    assert a.f(Other(), 'edit') == 'fallback'


def test_dispatch_external_predicates_ordering_before():
    class App(morepath.App):
        @delegate.on_external_predicates()
        def f(self, obj, name):
            return "fallback"

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.predicate(App.f, name='name', default='', index=KeyIndex)
    def pred_name(name):
        return name

    @App.predicate(App.f, name='model', default=None, index=ClassIndex,
                   before=pred_name)
    def pred_obj(obj):
        return obj.__class__

    @App.function(App.f, model=Foo, name='')
    def f_foo_default(obj, name):
        return "foo default"

    @App.function(App.f, model=Foo, name='edit')
    def f_foo_edit(obj, name):
        return "foo edit"

    @App.function(App.f, model=Bar, name='')
    def f_bar_default(obj, name):
        return "bar default"

    @App.function(App.f, model=Bar, name='edit')
    def f_bar_edit(obj, name):
        return "bar edit"

    a = App()
    a.commit()

    assert a.f(Foo(), '') == 'foo default'
    assert a.f(Bar(), '') == 'bar default'
    assert a.f(Foo(), 'edit') == 'foo edit'
    assert a.f(Bar(), 'edit') == 'bar edit'

    assert a.f(Other(), '') == 'fallback'
    assert a.f(Other(), 'edit') == 'fallback'


def test_dispatch_external_override_fallback():
    class App(morepath.App):
        @delegate.on_external_predicates()
        def f(self, obj):
            return "dispatch function"

    class Sub(App):
        pass

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.predicate(App.f, name='model', default=None, index=ClassIndex)
    def f_obj(obj):
        return obj.__class__

    @App.predicate_fallback(App.f, f_obj)
    def f_obj_fallback(obj):
        return "f_obj_fallback"

    @Sub.predicate_fallback(App.f, f_obj)
    def f_obj_fallback_sub(obj):
        return "f_obj_fallback sub"

    @App.function(App.f, model=Foo)
    def f_foo(obj):
        return "foo"

    @Sub.function(App.f, model=Foo)
    def f_foo_sub(obj):
        return "foo sub"

    @App.function(App.f, model=Bar)
    def f_bar(obj):
        return "bar"

    s = Sub()
    s.commit()

    assert s.f(Foo()) == 'foo sub'
    assert s.f(Bar()) == 'bar'
    assert s.f(Other()) == 'f_obj_fallback sub'

    # original is unaffected
    a = App()
    a.commit()

    assert a.f(Foo()) == 'foo'
    assert a.f(Bar()) == 'bar'
    assert a.f(Other()) == 'f_obj_fallback'


def test_dispatch_external_override_predicate():
    class App(morepath.App):
        @delegate.on_external_predicates()
        def f(self, obj):
            return "dispatch function"

    class Sub(App):
        pass

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.predicate(App.f, name='model', default=None, index=ClassIndex)
    def f_obj(obj):
        return obj.__class__

    @Sub.predicate(App.f, name='model', default=None, index=ClassIndex)
    def f_obj_sub(obj):
        return Bar  # ridiculous, but lets us test this

    @App.predicate_fallback(App.f, f_obj)
    def f_obj_fallback(obj):
        return "f_obj_fallback"

    @App.function(App.f, model=Foo)
    def f_foo(obj):
        return "foo"

    @Sub.function(App.f, model=Foo)
    def f_foo_sub(obj):
        return "foo"

    @App.function(App.f, model=Bar)
    def f_bar(obj):
        return "bar"

    @Sub.function(App.f, model=Bar)
    def f_bar_sub(obj):
        return "bar sub"

    s = Sub()
    s.commit()

    assert s.f(Foo()) == 'bar sub'
    assert s.f(Bar()) == 'bar sub'
    assert s.f(Other()) == 'bar sub'

    a = App()
    a.commit()

    assert a.f(Foo()) == 'foo'
    assert a.f(Bar()) == 'bar'
    assert a.f(Other()) == 'f_obj_fallback'


def test_wrong_predicate_arguments_single():
    class App(morepath.App):

        @delegate('obj')
        def f(self, obj):
            return "fallback"

    class Foo(object):
        pass

    # @App.function(App.f, obj=Foo)
    @App.function(App.f, wrong=Foo)
    def f_foo(obj):
        return "foo"

    a = App()
    a.commit()

    assert a.f(Foo()) == 'fallback'


def test_wrong_predicate_arguments_multi():
    class App(morepath.App):

        @delegate('a', 'b')
        def f(self, a, b):
            return "fallback"

    class Foo(object):
        pass

    # @App.function(App.f, a=Foo, b=Foo)
    @App.function(App.f, wrong=Foo)
    def f_foo(a, b):
        return "foo"

    a = App()
    a.commit()

    assert a.f(Foo(), Foo()) == 'fallback'


def test_predicate_not_for_dispatch_external_predicates():
    class App(morepath.App):

        @delegate('a')
        def f(self, a):
            pass

    @App.predicate(App.f, name='model', default=None, index=ClassIndex)
    def model_predicate(a):
        return a.__class__

    with pytest.raises(ConfigError):
        App().commit()


def test_dispatch_external_predicates_without_predicate_directives():
    class App(morepath.App):
        @delegate.on_external_predicates()
        def f(self, obj):
            return "fallback"

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.function(App.f)
    def f_foo(obj):
        return "foo"

    a = App()
    a.commit()

    assert a.f(Foo()) == 'foo'
