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
        pass

    MockApp.morepath = MockMorepathInfo('MockApp', [morepath.App], None, [])

    myapp = MockApp()
    lookup = myapp.lookup
    answer = lookup.component('foo', [])
    assert answer == 'answer'
    assert myapp.morepath.called == 1

    # after this the answer will be cached for those parameters
    answer = lookup.component('foo', [])
    assert myapp.morepath.called == 1

    answer = myapp.lookup.component('foo', [])
    assert myapp.morepath.called == 1

    # but different parameters does trigger another call
    lookup.component('bar', [])
    assert myapp.morepath.called == 2

