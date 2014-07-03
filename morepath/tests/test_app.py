import morepath
from morepath.app import MorepathInfo
from morepath.error import MountError
import morepath
import pytest


def setup_module(module):
    morepath.disable_implicit()


def test_app_caching_lookup():
    class MockMorepathInfo(MorepathInfo):
        called = 0

        def all(self, key, classes):
            self.called += 1
            return ["answer"]

    class MockApp(morepath.App):
        _info = None

        @classmethod
        def morepath(cls):
            if cls._info is not None:
                return cls._info
            result = cls._info = MockMorepathInfo(cls, [], cls.testing_config)
            return result

    myapp = MockApp()
    lookup = myapp.lookup
    answer = lookup.component('foo', [])
    assert answer == 'answer'
    assert myapp.morepath().called == 1

    # after this the answer will be cached for those parameters
    answer = lookup.component('foo', [])
    assert myapp.morepath().called == 1

    answer = myapp.lookup.component('foo', [])
    assert myapp.morepath().called == 1

    # but different parameters does trigger another call
    lookup.component('bar', [])
    assert myapp.morepath().called == 2


def test_app_set_implicit():
    app = morepath.App()
    app.set_implicit()

