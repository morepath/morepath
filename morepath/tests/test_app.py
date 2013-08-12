from morepath.app import App, global_app

def test_global_app():
    assert global_app.parent is None
    assert global_app.name == ''
    assert global_app.sub_apps == {}
    
