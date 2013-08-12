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
    assert parentapp.child_apps == { 'myapp': myapp }
