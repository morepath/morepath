from morepath.app import App, global_app
from morepath.error import MountError
import morepath
import pytest


def setup_module(module):
    morepath.disable_implicit()


def test_global_app():
    assert global_app.extends == []
    assert global_app.name == 'global_app'


def test_app_without_extends():
    myapp = App()
    assert myapp.extends == [global_app]
    assert myapp.name is None


def test_app_with_extends():
    parentapp = App()
    myapp = App('myapp', extends=parentapp)
    assert myapp.extends == [parentapp]
    assert myapp.name == 'myapp'


def test_app_caching_lookup():
    class MockClassLookup(object):
        called = 0

        def all(self, key, classes):
            self.called += 1
            return ["answer"]

    class MockApp(MockClassLookup, App):
        pass

    myapp = MockApp()
    lookup = myapp.lookup
    answer = lookup.component('foo', [])
    assert answer == 'answer'
    assert myapp.called == 1

    # after this the answer will be cached for those parameters
    answer = lookup.component('foo', [])
    assert myapp.called == 1

    answer = myapp.lookup.component('foo', [])
    assert myapp.called == 1

    # but different parameters does trigger another call
    lookup.component('bar', [])
    assert myapp.called == 2


def test_app_name_repr():
    app = morepath.App(name='foo')
    assert repr(app) == "<morepath.App 'foo'>"


def test_app_unnamed_repr():
    app = morepath.App()
    assert repr(app).startswith("<morepath.App at 0x")


def test_app_set_implicit():
    app = morepath.App()
    app.set_implicit()


def test_app_mounted():
    app = morepath.App(variables=['foo'])
    with pytest.raises(MountError):
        app.mounted()
