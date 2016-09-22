from reg import ClassIndex, KeyIndex
import morepath


def test_dispatch_method_directive():
    class App(morepath.App):
        @morepath.dispatch_method('obj')
        def f(self, obj):
            return "fallback"

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.method(App.f, obj=Foo)
    def f_foo(self, obj):
        return "foo"

    @App.method(App.f, obj=Bar)
    def f_bar(self, obj):
        return "bar"

    a = App()

    assert a.f(Foo()) == 'foo'
    assert a.f(Bar()) == 'bar'
    assert a.f(Other()) == 'fallback'


def test_dispatch_function_directive():
    class App(morepath.App):
        @morepath.dispatch_method('obj')
        def f(self, obj):
            return "fallback"

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.method(App.f, obj=Foo)
    def f_foo(app, obj):
        return "foo"

    @App.method(App.f, obj=Bar)
    def f_bar(app, obj):
        return "bar"

    a = App()

    assert a.f(Foo()) == 'foo'
    assert a.f(Bar()) == 'bar'
    assert a.f(Other()) == 'fallback'


def test_dispatch_external_predicates():
    class App(morepath.App):
        @morepath.dispatch_method()
        def f(app, obj):
            return "fallback"

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.predicate(App.f, name='model', default=None, index=ClassIndex)
    def f_obj(app, obj):
        return obj.__class__

    @App.method(App.f, model=Foo)
    def f_foo(app, obj):
        return "foo"

    @App.method(App.f, model=Bar)
    def f_bar(app, obj):
        return "bar"

    a = App()

    assert a.f(Foo()) == 'foo'
    assert a.f(Bar()) == 'bar'
    assert a.f(Other()) == 'fallback'


def test_dispatch_external_predicates_predicate_fallback():
    class App(morepath.App):
        @morepath.dispatch_method()
        def f(app, obj):
            return "dispatch function"

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.predicate(App.f, name='model', default=None, index=ClassIndex)
    def f_obj(app, obj):
        return obj.__class__

    @App.predicate_fallback(App.f, f_obj)
    def f_obj_fallback(app, obj):
        return "f_obj_fallback"

    @App.method(App.f, model=Foo)
    def f_foo(app, obj):
        return "foo"

    @App.method(App.f, model=Bar)
    def f_bar(app, obj):
        return "bar"

    a = App()

    assert a.f(Foo()) == 'foo'
    assert a.f(Bar()) == 'bar'
    assert a.f(Other()) == 'f_obj_fallback'


def test_dispatch_external_predicates_ordering_after():
    class App(morepath.App):
        @morepath.dispatch_method()
        def f(app, obj, name):
            return "fallback"

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.predicate(App.f, name='model', default=None, index=ClassIndex)
    def pred_obj(app, obj, name):
        return obj.__class__

    @App.predicate(App.f, name='name', default='', index=KeyIndex,
                   after=pred_obj)
    def pred_name(app, obj, name):
        return name

    @App.method(App.f, model=Foo, name='')
    def f_foo_default(app, obj, name):
        return "foo default"

    @App.method(App.f, model=Foo, name='edit')
    def f_foo_edit(app, obj, name):
        return "foo edit"

    @App.method(App.f, model=Bar, name='')
    def f_bar_default(app, obj, name):
        return "bar default"

    @App.method(App.f, model=Bar, name='edit')
    def f_bar_edit(app, obj, name):
        return "bar edit"

    a = App()

    assert a.f(Foo(), '') == 'foo default'
    assert a.f(Bar(), '') == 'bar default'
    assert a.f(Foo(), 'edit') == 'foo edit'
    assert a.f(Bar(), 'edit') == 'bar edit'

    assert a.f(Other(), '') == 'fallback'
    assert a.f(Other(), 'edit') == 'fallback'


def test_dispatch_external_predicates_ordering_before():
    class App(morepath.App):
        @morepath.dispatch_method()
        def f(app, obj, name):
            return "fallback"

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.predicate(App.f, name='name', default='', index=KeyIndex)
    def pred_name(app, obj, name):
        return name

    @App.predicate(App.f, name='model', default=None, index=ClassIndex,
                   before=pred_name)
    def pred_obj(app, obj, name):
        return obj.__class__

    @App.method(App.f, model=Foo, name='')
    def f_foo_default(app, obj, name):
        return "foo default"

    @App.method(App.f, model=Foo, name='edit')
    def f_foo_edit(app, obj, name):
        return "foo edit"

    @App.method(App.f, model=Bar, name='')
    def f_bar_default(app, obj, name):
        return "bar default"

    @App.method(App.f, model=Bar, name='edit')
    def f_bar_edit(app, obj, name):
        return "bar edit"

    a = App()

    assert a.f(Foo(), '') == 'foo default'
    assert a.f(Bar(), '') == 'bar default'
    assert a.f(Foo(), 'edit') == 'foo edit'
    assert a.f(Bar(), 'edit') == 'bar edit'

    assert a.f(Other(), '') == 'fallback'
    assert a.f(Other(), 'edit') == 'fallback'


def test_dispatch_external_override_fallback():
    class App(morepath.App):
        @morepath.dispatch_method()
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
    def f_obj(self, obj):
        return obj.__class__

    @App.predicate_fallback(App.f, f_obj)
    def f_obj_fallback(self, obj):
        return "f_obj_fallback"

    @Sub.predicate_fallback(App.f, f_obj)
    def f_obj_fallback_sub(self, obj):
        return "f_obj_fallback sub"

    @App.method(App.f, model=Foo)
    def f_foo(self, obj):
        return "foo"

    @Sub.method(App.f, model=Foo)
    def f_foo_sub(self, obj):
        return "foo sub"

    @App.method(App.f, model=Bar)
    def f_bar(self, obj):
        return "bar"

    s = Sub()

    assert s.f(Foo()) == 'foo sub'
    assert s.f(Bar()) == 'bar'
    assert s.f(Other()) == 'f_obj_fallback sub'

    # original is unaffected
    a = App()

    assert a.f(Foo()) == 'foo'
    assert a.f(Bar()) == 'bar'
    assert a.f(Other()) == 'f_obj_fallback'


def test_dispatch_external_override_predicate():
    class App(morepath.App):
        @morepath.dispatch_method()
        def f(app, obj):
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
    def f_obj(app, obj):
        return obj.__class__

    @Sub.predicate(App.f, name='model', default=None, index=ClassIndex)
    def f_obj_sub(app, obj):
        return Bar  # ridiculous, but lets us test this

    @App.predicate_fallback(App.f, f_obj)
    def f_obj_fallback(app, obj):
        return "f_obj_fallback"

    @App.method(App.f, model=Foo)
    def f_foo(app, obj):
        return "foo"

    @Sub.method(App.f, model=Foo)
    def f_foo_sub(app, obj):
        return "foo"

    @App.method(App.f, model=Bar)
    def f_bar(app, obj):
        return "bar"

    @Sub.method(App.f, model=Bar)
    def f_bar_sub(app, obj):
        return "bar sub"

    s = Sub()

    assert s.f(Foo()) == 'bar sub'
    assert s.f(Bar()) == 'bar sub'
    assert s.f(Other()) == 'bar sub'

    a = App()

    assert a.f(Foo()) == 'foo'
    assert a.f(Bar()) == 'bar'
    assert a.f(Other()) == 'f_obj_fallback'


def test_wrong_predicate_arguments_single():
    class App(morepath.App):
        @morepath.dispatch_method('obj')
        def f(self, obj):
            return "fallback"

    class Foo(object):
        pass

    @App.method(App.f, wrong=Foo)
    def f_foo(app, obj):
        return "foo"

    a = App()

    assert a.f(Foo()) == 'fallback'


def test_wrong_predicate_arguments_multi():
    class App(morepath.App):
        @morepath.dispatch_method('a', 'b')
        def f(self, a, b):
            return "fallback"

    class Foo(object):
        pass

    @App.method(App.f, wrong=Foo)
    def f_foo(app, a, b):
        return "foo"

    a = App()

    assert a.f(Foo(), Foo()) == 'fallback'


def test_dispatch_external_predicates_without_predicate_directives():
    class App(morepath.App):
        @morepath.dispatch_method()
        def f(self, obj):
            return "fallback"

    class Foo(object):
        pass

    class Bar(object):
        pass

    class Other(object):
        pass

    @App.method(App.f)
    def f_foo(app, obj):
        return "foo"

    a = App()

    assert a.f(Foo()) == 'foo'
