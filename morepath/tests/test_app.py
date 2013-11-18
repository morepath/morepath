from morepath.app import App, global_app


def test_global_app():
    assert global_app.parent is None
    assert global_app.name == ''
    assert global_app.child_apps == {}


def test_app_without_parent():
    myapp = App()
    assert myapp.parent is None
    assert myapp.name == ''
    assert myapp.child_apps == {}
    assert global_app.child_apps == {}


def test_app_with_parent():
    parentapp = App()
    myapp = App('myapp', parent=parentapp)
    assert myapp.parent is parentapp
    assert myapp.name == 'myapp'
    assert myapp.child_apps == {}
    assert parentapp.child_apps == {'myapp': myapp}


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
