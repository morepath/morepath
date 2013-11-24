from morepath.app import App, global_app


def test_global_app():
    assert global_app.extends is None
    assert global_app.name == ''


def test_app_without_extends():
    myapp = App()
    assert myapp.extends is None
    assert myapp.name == ''


def test_app_with_extends():
    parentapp = App()
    myapp = App('myapp', extends=parentapp)
    assert myapp.extends is parentapp
    assert myapp.name == 'myapp'


def test_app_caching_lookup():
    class MockClassLookup(object):
        called = 0

        def all(self, key, classes):
            self.called += 1
            return ["answer"]
    mock_class_lookup = MockClassLookup()

    class MockApp(App):
        def class_lookup(self):
            return mock_class_lookup

    myapp = MockApp()
    lookup = myapp.lookup()
    answer = lookup.component('foo', [])
    assert answer == 'answer'
    assert mock_class_lookup.called == 1

    # after this the answer will be cached for those parameters
    answer = lookup.component('foo', [])
    assert mock_class_lookup.called == 1

    answer = myapp.lookup().component('foo', [])
    assert mock_class_lookup.called == 1

    # but different parameters does trigger another call
    lookup.component('bar', [])
    assert mock_class_lookup.called == 2
