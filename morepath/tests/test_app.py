from morepath.app import App, global_app


def test_global_app():
    assert global_app.extends == []
    assert global_app.name == 'global_app'


def test_app_without_extends():
    myapp = App()
    assert myapp.extends == [global_app]
    assert myapp.name == ''


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
    lookup = myapp.lookup()
    answer = lookup.component('foo', [])
    assert answer == 'answer'
    assert myapp.called == 1

    # after this the answer will be cached for those parameters
    answer = lookup.component('foo', [])
    assert myapp.called == 1

    answer = myapp.lookup().component('foo', [])
    assert myapp.called == 1

    # but different parameters does trigger another call
    lookup.component('bar', [])
    assert myapp.called == 2
