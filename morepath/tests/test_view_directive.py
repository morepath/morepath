import morepath
from werkzeug.test import Client


def test_view_get_only():
    config = morepath.setup()
    app = morepath.App(testing_config=config)

    @app.model(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.view(model=Model)
    def default(request, model):
        return "View"
    config.commit()

    c = Client(app, morepath.Response)

    response = c.get('/')
    assert response.data == 'View'

    # XXX should be giving 405 method not allowed
    response = c.post('/')
    assert response.status == '404 NOT FOUND'


def test_view_any():
    config = morepath.setup()
    app = morepath.App(testing_config=config)

    @app.model(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.view(model=Model, request_method=morepath.ANY)
    def default(request, model):
        return "View"
    config.commit()

    c = Client(app, morepath.Response)

    response = c.get('/')
    assert response.data == 'View'

    response = c.post('/')
    assert response.data == 'View'

