import morepath


def test_code_info():
    class App(morepath.App):
        pass

    @App.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @App.view(model=Model)
    def default(self, request):
        return "View"

    App.commit()
    app = App()

    r = morepath.Request.blank('/', method='GET', app=app)
    app.publish(r)
    assert r.path_code_info is not None
    assert r.path_code_info.sourceline == "@App.path(path='')"
    assert r.view_code_info is not None
    assert r.view_code_info.sourceline == "@App.view(model=Model)"


def test_code_info_no_path():
    class App(morepath.App):
        pass

    App.commit()
    app = App()

    r = morepath.Request.blank('/', method='GET', app=app)
    app.publish(r)
    assert r.path_code_info is None
    assert r.view_code_info is not None
