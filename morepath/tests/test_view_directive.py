import morepath
from morepath.error import ConflictError
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse as Response
import pytest


def setup_module(module):
    morepath.disable_implicit()


def test_view_get_only():
    config = morepath.setup()
    app = morepath.App(testing_config=config)

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.view(model=Model)
    def default(self, request):
        return "View"
    config.commit()

    c = Client(app, Response)

    response = c.get('/')
    assert response.data == 'View'

    response = c.post('/')
    assert response.status == '405 Method Not Allowed'


def test_view_any():
    config = morepath.setup()
    app = morepath.App(testing_config=config)

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.view(model=Model, request_method=morepath.ANY)
    def default(self, request):
        return "View"
    config.commit()

    c = Client(app, Response)

    response = c.get('/')
    assert response.data == 'View'

    response = c.post('/')
    assert response.data == 'View'


def test_view_name_conflict_involving_default():
    config = morepath.setup()
    app = morepath.App(testing_config=config)

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.view(model=Model)
    def default(self, request):
        return "View"

    @app.view(model=Model, name='')
    def default2(self, request):
        return "View"

    with pytest.raises(ConflictError):
        config.commit()


def test_view_custom_predicate_conflict_involving_default_extends():
    config = morepath.setup()
    core = morepath.App(testing_config=config)
    app = morepath.App(testing_config=config, extends=core)

    @core.predicate(name='foo', order=100, default='DEFAULT')
    def get_foo(request, model):
        return 'foo'

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.view(model=Model)
    def default(self, request):
        return "View"

    @app.view(model=Model, foo='DEFAULT')
    def default2(self, request):
        return "View"

    with pytest.raises(ConflictError):
        config.commit()
