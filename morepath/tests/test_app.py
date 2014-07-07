import morepath
from morepath.app import Registry


def setup_module(module):
    morepath.disable_implicit()


def test_app_caching_lookup():
    class MockRegistry(Registry):
        called = 0

        def all(self, key, classes):
            self.called += 1
            return ["answer"]

    class MockApp(morepath.App):
        pass

    MockApp.registry = MockRegistry('MockApp', [morepath.App], None, [])

    myapp = MockApp()
    lookup = myapp.lookup
    answer = lookup.component('foo', [])
    assert answer == 'answer'
    assert myapp.registry.called == 1

    # after this the answer will be cached for those parameters
    answer = lookup.component('foo', [])
    assert myapp.registry.called == 1

    answer = myapp.lookup.component('foo', [])
    assert myapp.registry.called == 1

    # but different parameters does trigger another call
    lookup.component('bar', [])
    assert myapp.registry.called == 2
